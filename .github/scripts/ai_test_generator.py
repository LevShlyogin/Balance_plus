# .github/scripts/ai_test_generator.py
import os
import re
import subprocess
import requests
from github import Github
from pathlib import Path

OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"
MAX_SOURCE_CHARS = 50000

# Маппинг расширений на языки и фреймворки
LANG_CONFIG = {
    ".py": {
        "lang": "python",
        "framework": "pytest",
        "test_dir": "tests",
        "test_prefix": "test_",
    },
    ".js": {
        "lang": "javascript",
        "framework": "jest",
        "test_dir": "__tests__",
        "test_suffix": ".test.js",
    },
    ".ts": {
        "lang": "typescript",
        "framework": "jest",
        "test_dir": "__tests__",
        "test_suffix": ".test.ts",
    },
    ".tsx": {
        "lang": "typescript",
        "framework": "jest",
        "test_dir": "__tests__",
        "test_suffix": ".test.tsx",
    },
    ".go": {
        "lang": "go",
        "framework": "go test",
        "test_dir": "",
        "test_suffix": "_test.go",
    },
    ".java": {
        "lang": "java",
        "framework": "junit",
        "test_dir": "src/test/java",
        "test_prefix": "Test",
    },
    ".rs": {
        "lang": "rust",
        "framework": "cargo test",
        "test_dir": "",
        "test_suffix": "",
    },
}

# Паттерн для определения тестовых файлов
TEST_FILE_PATTERN = re.compile(
    r'[_/\\]tests?[_/\\.]|'
    r'[_/\\]specs?[_/\\.]|'
    r'^tests?[_/\\]|'
    r'[_/\\]__tests__[_/\\]|'
    r'\.test\.|'
    r'\.spec\.|'
    r'_test\.|'
    r'_spec\.',
    re.IGNORECASE
)


def load_test_prompt():
    """Загружаем системный промт из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "test_generator_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    print("Warning: test_generator_prompt.md not found, using default")
    return get_default_prompt()


def get_default_prompt():
    """Дефолтный промпт если файл не найден"""
    return (
        "You are a Senior Software Engineer specializing in testing.\n"
        "Write comprehensive unit tests for the provided code.\n"
        "Cover all public functions, edge cases, and use mocks where needed.\n"
        "Return ONLY the test code, no explanations."
    )


def read_file_safe(path):
    """Безопасное чтение файла с заменой невалидных символов"""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            if "\ufffd" in content:
                print(f"Warning: {path} contains invalid UTF-8 characters (replaced)")
            return content
    except FileNotFoundError:
        print(f"Warning: File not found: {path}")
        return None
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def call_openrouter(system_prompt, user_prompt):
    """Вызов OpenRouter API"""
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
    # Паттерн для code blocks с опциональным языком
    pattern = r"```(?:[\w+-]*)?\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Объединяем все блоки кода
        code = "\n\n".join(m.strip() for m in matches if m.strip())
        return code
    
    # Если нет code blocks, возвращаем как есть (убирая markdown)
    # Удаляем строки которые выглядят как заголовки/списки
    lines = []
    for line in text.split("\n"):
        if not line.startswith("#") and not line.startswith("-") and not line.startswith("*"):
            lines.append(line)
    return "\n".join(lines)


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
    match = re.search(r"/generate-tests\s+(.*)", comment_body, re.IGNORECASE)
    if match:
        files_str = match.group(1).strip()
        if files_str:
            # Разбиваем по пробелам, но учитываем пути с пробелами в кавычках
            files = re.findall(r'["\']([^"\']+)["\']|(\S+)', files_str)
            return [f[0] or f[1] for f in files if f[0] or f[1]]
    return None


def is_test_file(filepath):
    """Проверяет, является ли файл тестовым"""
    return bool(TEST_FILE_PATTERN.search(filepath))


def filter_source_files(files_list):
    """Фильтрует только исходные файлы (не тесты, не конфиги)"""
    source_files = []
    skip_dirs = {
        "__pycache__", "node_modules", ".git", "venv", ".venv",
        "env", ".env", "dist", "build", ".tox", ".pytest_cache",
        ".mypy_cache", "htmlcov", ".coverage"
    }
    
    for f in files_list:
        f = f.strip()
        if not f:
            continue
        
        # Пропускаем тестовые файлы (улучшенный regex)
        if is_test_file(f):
            print(f"  Skipping test file: {f}")
            continue
        
        # Пропускаем служебные директории
        path_parts = Path(f).parts
        if any(part in skip_dirs for part in path_parts):
            print(f"  Skipping (skip dir): {f}")
            continue
        
        # Только поддерживаемые расширения
        ext = Path(f).suffix.lower()
        if ext in LANG_CONFIG:
            source_files.append(f)
        else:
            print(f"  Skipping (unsupported ext): {f}")
    
    return source_files


def git_commit_and_push(generated_tests, head_ref, is_fork):
    """Коммитит и пушит сгенерированные тесты"""
    if is_fork:
        print("Cannot push to fork, skipping git operations")
        return False
    
    # Настраиваем git
    subprocess.run(
        ["git", "config", "user.name", "github-actions[bot]"],
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True
    )
    
    # Добавляем файлы
    for item in generated_tests:
        subprocess.run(["git", "add", item["test"]], check=True)
    
    # Проверяем есть ли что коммитить
    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("No changes to commit")
        return False
    
    # Формируем сообщение коммита
    files_list = "\n".join(
        [f"- {item['source']} -> {item['test']}" for item in generated_tests]
    )
    commit_msg = f"test: add AI-generated tests\n\n{files_list}"
    
    # Коммитим
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    
    # Пушим
    push_result = subprocess.run(
        ["git", "push", "origin", f"HEAD:{head_ref}"],
        capture_output=True,
        text=True
    )
    
    if push_result.returncode != 0:
        print(f"Push failed: {push_result.stderr}")
        return False
    
    print("Successfully pushed changes")
    return True


def main():
    print("=" * 60)
    print("AI Test Generator")
    print("=" * 60)
    
    mode = os.environ.get("MODE", "comment")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("REPO_NAME")
    is_fork = os.environ.get("IS_FORK", "false").lower() == "true"
    
    if not github_token:
        print("Error: GITHUB_TOKEN not set")
        return 1
    
    if not repo_name:
        print("Error: REPO_NAME not set")
        return 1
    
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)
    
    # Определяем файлы для генерации тестов
    if mode == "manual":
        target_file = os.environ.get("TARGET_FILE")
        framework_override = os.environ.get("TEST_FRAMEWORK")
        if not target_file:
            print("Error: TARGET_FILE not specified")
            return 1
        files_to_process = [target_file]
        print(f"Manual mode: processing {target_file}")
    else:
        comment_body = os.environ.get("COMMENT_BODY", "")
        specified_files = parse_files_from_comment(comment_body)
        
        if specified_files:
            files_to_process = specified_files
            print(f"Files from comment: {specified_files}")
        else:
            changed_files = read_file_safe("changed_files.txt") or ""
            files_to_process = filter_source_files(changed_files.split("\n"))
            print(f"Files from PR diff: {files_to_process}")
        
        framework_override = None
    
    if not files_to_process:
        print("No source files to process")
        if mode != "manual":
            pr_number = int(os.environ.get("PR_NUMBER", 0))
            if pr_number:
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(
                    "⚠️ **AI Test Generator:** Не найдено подходящих файлов для генерации тестов.\n\n"
                    "Укажите файлы явно: `/generate-tests path/to/file.py`\n\n"
                    "Поддерживаемые расширения: `.py`, `.js`, `.ts`, `.tsx`, `.go`, `.java`, `.rs`"
                )
        return 0
    
    print(f"\nFiles to process: {files_to_process}")
    
    system_prompt = load_test_prompt()
    generated_tests = []
    skipped_existing = []
    errors = []
    
    for file_path in files_to_process:
        print(f"\n{'─' * 40}")
        print(f"Processing: {file_path}")
        
        # Читаем исходный код
        source_code = read_file_safe(file_path)
        if not source_code:
            print(f"Cannot read {file_path}, skipping")
            errors.append({"file": file_path, "error": "Cannot read file"})
            continue
        
        # Ограничиваем размер
        if len(source_code) > MAX_SOURCE_CHARS:
            print(f"Warning: {file_path} is too large, truncating")
            source_code = source_code[:MAX_SOURCE_CHARS] + "\n\n# ... TRUNCATED ..."
        
        # Определяем конфигурацию
        ext = Path(file_path).suffix.lower()
        config = LANG_CONFIG.get(ext, LANG_CONFIG[".py"]).copy()
        
        if framework_override:
            config["framework"] = framework_override
        
        # Определяем путь для тестов
        test_path = get_test_file_path(file_path, config)
        
        # Проверяем существующий файл
        if test_path.exists():
            print(f"Test file already exists: {test_path}")
            skipped_existing.append({"source": file_path, "test": str(test_path)})
            continue
        
        # Формируем запрос
        user_prompt = (
            "## Task\n\n"
            f"Write unit tests for the following file.\n\n"
            f"**File:** `{file_path}`\n"
            f"**Language:** {config['lang']}\n"
            f"**Framework:** {config['framework']}\n\n"
            "## Source Code\n\n"
            f"```{config['lang']}\n{source_code}\n```\n\n"
            "## Requirements\n\n"
            "1. Cover all public functions/methods\n"
            "2. Include edge cases (empty values, errors, boundaries)\n"
            "3. Use mocks for external dependencies (DB, API, filesystem)\n"
            "4. Code must be ready to run\n"
            "5. Add docstrings/comments explaining each test\n"
            "6. Follow the framework's best practices\n\n"
            "Return ONLY the test code, no explanations."
        )
        
        try:
            print("Calling AI model...")
            response = call_openrouter(system_prompt, user_prompt)
            test_code = extract_code_blocks(response)
            
            # Проверяем что получили код
            if not test_code.strip():
                print(f"Warning: Empty test code for {file_path}")
                errors.append({"file": file_path, "error": "Empty response from AI"})
                continue
            
            # Создаём директорию если нужно
            test_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем тесты
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            print(f"Generated: {test_path} ({len(test_code)} chars)")
            generated_tests.append({"source": file_path, "test": str(test_path)})
            
        except Exception as e:
            print(f"Error generating tests for {file_path}: {e}")
            errors.append({"file": file_path, "error": str(e)})
    
    print(f"\n{'=' * 60}")
    print(f"Summary: {len(generated_tests)} generated, {len(skipped_existing)} skipped, {len(errors)} errors")
    
    # Если это комментарий в PR — коммитим и постим результат
    if mode != "manual":
        pr_number = int(os.environ.get("PR_NUMBER", 0))
        head_ref = os.environ.get("HEAD_REF", "main")
        
        if pr_number and generated_tests:
            # Коммитим и пушим
            pushed = git_commit_and_push(generated_tests, head_ref, is_fork)
            
            # Формируем комментарий
            pr = repo.get_pull(pr_number)
            
            # Таблица сгенерированных
            gen_table = "\n".join([
                f"| `{item['source']}` | `{item['test']}` | ✅ |"
                for item in generated_tests
            ])
            
            # Таблица пропущенных
            skip_table = ""
            if skipped_existing:
                skip_rows = "\n".join([
                    f"| `{item['source']}` | `{item['test']}` | ⏭️ Exists |"
                    for item in skipped_existing
                ])
                skip_table = f"\n\n### Пропущенные (тесты уже существуют)\n\n| Файл | Тест | Статус |\n|------|------|--------|\n{skip_rows}"
            
            # Таблица ошибок
            err_table = ""
            if errors:
                err_rows = "\n".join([
                    f"| `{item['file']}` | {item['error'][:50]} |"
                    for item in errors
                ])
                err_table = f"\n\n### Ошибки\n\n| Файл | Ошибка |\n|------|--------|\n{err_rows}"
            
            push_status = "✅ Изменения запушены в ветку" if pushed else "⚠️ Изменения не запушены (fork или ошибка)"
            
            comment = (
                "## 🧪 AI Test Generator\n\n"
                f"{push_status}\n\n"
                "### Сгенерированные тесты\n\n"
                "| Исходный файл | Файл тестов | Статус |\n"
                "|---------------|-------------|--------|\n"
                f"{gen_table}"
                f"{skip_table}"
                f"{err_table}\n\n"
                "---\n\n"
                "> ⚠️ **Важно:** Тесты сгенерированы AI и могут содержать ошибки!\n\n"
                "**Проверьте перед мержем:**\n"
                "```bash\n"
                "pytest  # или ваша команда\n"
                "```"
            )
            
            pr.create_issue_comment(comment)
            print("Comment posted!")
    
    return 0


if __name__ == "__main__":
    exit(main())
