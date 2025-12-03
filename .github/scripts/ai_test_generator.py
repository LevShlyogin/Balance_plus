# .github/scripts/ai_test_generator.py
import os
import re
import requests
from github import Github
from pathlib import Path

OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"

# Маппинг расширений на языки и фреймворки
LANG_CONFIG = {
    ".py": {"lang": "python", "framework": "pytest", "test_dir": "tests", "test_prefix": "test_"},
    ".js": {"lang": "javascript", "framework": "jest", "test_dir": "__tests__", "test_suffix": ".test.js"},
    ".ts": {"lang": "typescript", "framework": "jest", "test_dir": "__tests__", "test_suffix": ".test.ts"},
    ".tsx": {"lang": "typescript", "framework": "jest", "test_dir": "__tests__", "test_suffix": ".test.tsx"},
    ".go": {"lang": "go", "framework": "go test", "test_dir": "", "test_suffix": "_test.go"},
    ".java": {"lang": "java", "framework": "junit", "test_dir": "src/test/java", "test_prefix": "Test"},
    ".rs": {"lang": "rust", "framework": "cargo test", "test_dir": "", "test_suffix": ""},
}


def load_test_prompt():
    prompt_path = Path(__file__).parent.parent / "prompts" / "test_generator_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return get_default_prompt()


def get_default_prompt():
    return """Ты — Senior Software Engineer, специалист по тестированию.
Напиши unit-тесты для предоставленного кода.
Тесты должны быть полными, покрывать edge cases и быть готовыми к запуску."""


def read_file_safe(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def call_openrouter(system_prompt, user_prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "GitHub AI Test Generator",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 16384,
        },
        timeout=180,
    )

    print(f"OpenRouter status: {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text[:500]}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_code_blocks(text):
    """Извлекает код из markdown блоков"""
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return "\n\n".join(matches)
    return text


def get_test_file_path(source_path, config):
    """Определяет путь для файла с тестами"""
    source = Path(source_path)
    name = source.stem
    ext = source.suffix
    
    if config.get("test_prefix"):
        test_name = f"{config['test_prefix']}{name}{ext}"
    elif config.get("test_suffix"):
        test_name = f"{name}{config['test_suffix']}"
    else:
        test_name = f"test_{name}{ext}"
    
    if config.get("test_dir"):
        # Сохраняем структуру папок
        relative_parent = source.parent
        test_dir = Path(config["test_dir"]) / relative_parent
        return test_dir / test_name
    else:
        # Тесты рядом с исходником (Go style)
        return source.parent / test_name


def parse_files_from_comment(comment_body):
    """Извлекает файлы из комментария /generate-tests file1.py file2.py"""
    match = re.search(r"/generate-tests\s+(.*)", comment_body)
    if match:
        files_str = match.group(1).strip()
        if files_str:
            return [f.strip() for f in files_str.split() if f.strip()]
    return None


def filter_source_files(files_list):
    """Фильтрует только исходные файлы (не тесты, не конфиги)"""
    source_files = []
    for f in files_list:
        f = f.strip()
        if not f:
            continue
        # Пропускаем тесты
        if "test" in f.lower() or "spec" in f.lower():
            continue
        # Пропускаем конфиги и прочее
        if any(skip in f for skip in ["__pycache__", "node_modules", ".git", "venv", ".env"]):
            continue
        # Только поддерживаемые расширения
        ext = Path(f).suffix
        if ext in LANG_CONFIG:
            source_files.append(f)
    return source_files


def main():
    print("🧪 Starting AI Test Generator...")
    
    mode = os.environ.get("MODE", "comment")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("REPO_NAME")
    
    if not all([github_token, repo_name]):
        print("❌ Missing environment variables!")
        return 1
    
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)
    
    # Определяем файлы для генерации тестов
    if mode == "manual":
        # Ручной запуск — один файл
        target_file = os.environ.get("TARGET_FILE")
        framework_override = os.environ.get("TEST_FRAMEWORK")
        if not target_file:
            print("❌ TARGET_FILE not specified")
            return 1
        files_to_process = [target_file]
    else:
        # Из комментария или из списка изменённых файлов
        comment_body = os.environ.get("COMMENT_BODY", "")
        specified_files = parse_files_from_comment(comment_body)
        
        if specified_files:
            files_to_process = specified_files
        else:
            # Все изменённые файлы из PR
            changed_files = read_file_safe("changed_files.txt") or ""
            files_to_process = filter_source_files(changed_files.split("\n"))
        
        framework_override = None
    
    if not files_to_process:
        print("⚠️ No source files to process")
        # Оставляем комментарий в PR
        if mode != "manual":
            pr_number = int(os.environ.get("PR_NUMBER", 0))
            if pr_number:
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(
                    "⚠️ **AI Test Generator:** Не найдено подходящих файлов для генерации тестов.\n\n"
                    "Укажите файлы явно: `/generate-tests path/to/file.py`"
                )
        return 0
    
    print(f"📁 Files to process: {files_to_process}")
    
    system_prompt = load_test_prompt()
    generated_tests = []
    
    for file_path in files_to_process:
        print(f"\n📄 Processing: {file_path}")
        
        # Читаем исходный код
        source_code = read_file_safe(file_path)
        if not source_code:
            print(f"⚠️ Cannot read {file_path}, skipping")
            continue
        
        # Определяем конфигурацию
        ext = Path(file_path).suffix
        config = LANG_CONFIG.get(ext, LANG_CONFIG[".py"])
        
        if framework_override:
            config["framework"] = framework_override
        
        # Формируем запрос
        user_prompt = (
            f"## Задача\n\n"
            f"Напиши unit-тесты для следующего файла.\n\n"
            f"**Файл:** `{file_path}`\n"
            f"**Язык:** {config['lang']}\n"
            f"**Фреймворк:** {config['framework']}\n\n"
            f"## Исходный код\n\n"
            f"```{config['lang']}\n{source_code}\n```\n\n"
            f"## Требования\n\n"
            f"1. Покрой все публичные функции/методы\n"
            f"2. Добавь тесты на edge cases (пустые значения, ошибки)\n"
            f"3. Используй моки где нужно (внешние зависимости, БД, API)\n"
            f"4. Код должен быть готов к запуску\n"
            f"5. Добавь docstrings к тестам\n\n"
            f"Верни ТОЛЬКО код тестов, без объяснений."
        )
        
        try:
            print("🤖 Calling Grok...")
            response = call_openrouter(system_prompt, user_prompt)
            test_code = extract_code_blocks(response)
            
            # Определяем путь для тестов
            test_path = get_test_file_path(file_path, config)
            
            # Создаём директорию если нужно
            test_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем тесты
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            print(f"✅ Generated: {test_path}")
            generated_tests.append({"source": file_path, "test": str(test_path)})
            
        except Exception as e:
            print(f"❌ Error generating tests for {file_path}: {e}")
    
    # Если это комментарий в PR — постим результат и коммитим
    if mode != "manual" and generated_tests:
        pr_number = int(os.environ.get("PR_NUMBER", 0))
        head_ref = os.environ.get("HEAD_REF", "main")
        
        if pr_number:
            # Коммитим сгенерированные тесты
            import subprocess
            
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            
            for item in generated_tests:
                subprocess.run(["git", "add", item["test"]], check=True)
            
            commit_msg = "test: add AI-generated tests\n\n" + "\n".join(
                [f"- {item['source']} → {item['test']}" for item in generated_tests]
            )
            
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push", "origin", f"HEAD:{head_ref}"], check=True)
            
            # Комментарий в PR
            pr = repo.get_pull(pr_number)
            
            table = "\n".join([
                f"| `{item['source']}` | `{item['test']}` |" 
                for item in generated_tests
            ])
            
            comment = (
                "## 🧪 AI Test Generator\n\n"
                "Сгенерированы тесты и добавлены в ветку:\n\n"
                "| Исходный файл | Файл тестов |\n"
                "|---------------|-------------|\n"
                f"{table}\n\n"
                "> ⚠️ **Проверьте тесты!** AI может генерировать некорректные или неполные тесты.\n\n"
                "Запустите локально:\n"
                "```bash\npytest  # или ваша команда\n```"
            )
            
            pr.create_issue_comment(comment)
            print("✅ Comment posted and tests committed!")
    
    return 0


if __name__ == "__main__":
    exit(main())
