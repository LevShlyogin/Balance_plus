import os
import requests
from github import Github
from pathlib import Path

OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"
MAX_DIFF_CHARS = 100000


def load_system_prompt():
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "Ты — Senior Software Engineer. Проведи код-ревью на русском языке."


def read_file_safe(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def truncate_diff(diff, max_chars=MAX_DIFF_CHARS):
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + "\n\n... [TRUNCATED] ..."


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
            "X-Title": "GitHub AI Code Reviewer",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        },
        timeout=120,
    )

    print(f"OpenRouter status: {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text[:500]}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def main():
    print("Starting AI Code Review...")

    github_token = os.environ.get("GITHUB_TOKEN")
    pr_number = int(os.environ.get("PR_NUMBER", 0))
    repo_name = os.environ.get("REPO_NAME", "")
    pr_title = os.environ.get("PR_TITLE", "Untitled")
    pr_body = os.environ.get("PR_BODY") or "No description"
    pr_author = os.environ.get("PR_AUTHOR", "unknown")

    if not all([github_token, pr_number, repo_name]):
        print("Missing environment variables!")
        return 1

    diff = read_file_safe("pr_diff.txt")
    changed_files = read_file_safe("changed_files.txt")

    if not diff.strip():
        print("Empty diff, skipping")
        return 0

    print(f"Diff size: {len(diff)} chars")

    system_prompt = load_system_prompt()

    user_prompt = (
        "## Pull Request для ревью\n\n"
        f"**Автор:** @{pr_author}\n"
        f"**Название:** {pr_title}\n\n"
        f"**Описание:**\n{pr_body}\n\n"
        "---\n\n"
        f"**Изменённые файлы:**\n```\n{changed_files}\n```\n\n"
        f"**Diff:**\n```diff\n{truncate_diff(diff)}\n```\n\n"
        "---\n\nПроведи код-ревью этого PR."
    )

    print("Calling Grok...")

    try:
        review_text = call_openrouter(system_prompt, user_prompt)
        print("Got review")
    except Exception as e:
        review_text = f"**Ошибка:** {e}"
        print(f"Error: {e}")

    print("Posting comment...")

    try:
        gh = Github(github_token)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        comment = (
            "## 🤖 AI Code Review\n\n"
            f"{review_text}\n\n"
            "---\n"
            "<sub>Grok 4.1 via OpenRouter</sub>"
        )

        pr.create_issue_comment(comment)
        print("Comment posted!")

    except Exception as e:
        print(f"Failed to post: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
