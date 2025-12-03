# .github/scripts/ai_reviewer.py
import os
import json
import requests
from github import Github
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"
MAX_DIFF_CHARS = 100000


# ═══════════════════════════════════════════════════════════════
# ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════

def load_system_prompt() -> str:
    """Загружаем системный промт из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding='utf-8')
    print("⚠️ System prompt not found, using default")
    return "Ты — Senior Software Engineer. Проведи код-ревью на русском языке."


def read_file_safe(path: str) -> str:
    """Безопасное чтение файла"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Cannot read {path}: {e}")
        return ""


def truncate_diff(diff: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    """Обрезаем diff если слишком большой"""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n... [ОБРЕЗАНО, показано первые {max_chars} символов] ..."


def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    """Вызов OpenRouter API"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не установлен!")
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "GitHub AI Code Reviewer",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        },
        timeout=120
    )
    
    print(f"📡 OpenRouter response status: {response.status_code}")
    
    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text[:500]}")
    
    data = response.json()
    return data['choices'][0]['message']['content']


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("🚀 Starting AI Code Review with Grok...")
    
    # Переменные окружения
    github_token = os.environ.get('GITHUB_TOKEN')
    pr_number = int(os.environ.get('PR_NUMBER', 0))
    repo_name = os.environ.get('REPO_NAME', '')
    pr_title = os.environ.get('PR_TITLE', 'Без названия')
    pr_body = os.environ.get('PR_BODY') or 'Описание отсутствует'
    pr_author = os.environ.get('PR_AUTHOR', 'unknown')
    
    if not all([github_token, pr_number, repo_name]):
        print("❌ Missing environment variables!")
        return 1
    
    # Читаем diff
    diff = read_file_safe('pr_diff.txt')
    changed_files = read_file_safe('changed_files.txt')
    
    if not diff.strip():
        print("⚠️ Empty diff, skipping review")
        return 0
    
    print(f"📄 Diff size: {len(diff)} chars")
    print(f"📁 Files:\n{changed_files}")
    
    # Загружаем промт
    system_prompt = load_system_prompt()
    
    # Формируем запрос
    user_prompt = f"""## Pull Request для ревью

**Автор:** @{pr_author}
**Название:** {pr_title}

**Описание:**
{pr_body}

---

**Изменённые файлы:**
