# gitlab_adapter.py — ДОПОЛНЯЕМ существующий файл
import os
import gitlab
from gitlab.exceptions import GitlabGetError
from dotenv import load_dotenv

load_dotenv()


class GitLabAdapter:
    def __init__(self):
        self.url = os.getenv("GITLAB_URL")
        self.token = os.getenv("GITLAB_PRIVATE_TOKEN")
        self.project_id = os.getenv("GITLAB_PROJECT_ID")

        if not self.url or not self.token:
            raise ValueError("В файле .env не заданы настройки GitLab")

        self.gl = gitlab.Gitlab(self.url, private_token=self.token, ssl_verify=False)
        self._project = None
        self._default_branch = None

    def check_connection(self) -> str:
        try:
            self.gl.auth()
            return f"OK: {self.gl.user.username}"
        except Exception as e:
            return f"Error: {e}"

    def get_project(self):
        """Получает объект текущего рабочего проекта (с кешированием)"""
        if self._project is None:
            if not self.project_id:
                raise ValueError("GITLAB_PROJECT_ID не задан в .env")
            self._project = self.gl.projects.get(self.project_id)
            self._default_branch = self._project.default_branch
            print(f"📌 Подключён к проекту: {self._project.path_with_namespace}")
            print(f"📌 Дефолтная ветка: {self._default_branch}")
        return self._project

    @property
    def default_branch(self) -> str:
        """Возвращает дефолтную ветку проекта"""
        if self._default_branch is None:
            self.get_project()
        return self._default_branch

    # ==================== РАБОТА С ФАЙЛАМИ ====================

    def get_file_content(self, file_path: str, ref: str | None = None) -> str:
        """Читает содержимое файла из репозитория"""
        project = self.get_project()
        ref = ref or self.default_branch
        file = project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode("utf-8")

    def file_exists(self, file_path: str, ref: str | None = None) -> bool:
        """Проверяет, существует ли файл"""
        project = self.get_project()
        ref = ref or self.default_branch
        try:
            project.files.get(file_path=file_path, ref=ref)
            return True
        except GitlabGetError:
            return False

    def create_commit(self, file_path: str, content: str, commit_message: str, branch: str | None = None):
        """Создает или обновляет файл в репозитории"""
        project = self.get_project()
        branch = branch or self.default_branch

        action = "update" if self.file_exists(file_path, branch) else "create"

        data = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [{"action": action, "file_path": file_path, "content": content}],
        }

        commit = project.commits.create(data)
        return commit

    def create_commit_multiple(
        self, files: dict[str, str], commit_message: str, branch: str | None = None
    ):
        """Создает коммит с несколькими файлами одновременно"""
        project = self.get_project()
        branch = branch or self.default_branch

        actions = []
        for file_path, content in files.items():
            action = "update" if self.file_exists(file_path, branch) else "create"
            actions.append({"action": action, "file_path": file_path, "content": content})

        data = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": actions,
        }

        commit = project.commits.create(data)
        return commit

    # ==================== РАБОТА С ВЕТКАМИ ====================

    def create_branch(self, branch_name: str, source_branch: str | None = None) -> bool:
        """Создаёт новую ветку. Возвращает True если создана, False если уже существует"""
        project = self.get_project()
        source = source_branch or self.default_branch

        try:
            project.branches.create({"branch": branch_name, "ref": source})
            print(f"✅ Создана ветка: {branch_name}")
            return True
        except gitlab.exceptions.GitlabCreateError as e:
            if "already exists" in str(e):
                print(f"ℹ️ Ветка {branch_name} уже существует")
                return False
            raise

    def branch_exists(self, branch_name: str) -> bool:
        """Проверяет существование ветки"""
        project = self.get_project()
        try:
            project.branches.get(branch_name)
            return True
        except GitlabGetError:
            return False

    # ==================== РАБОТА С ЗАДАЧАМИ (ISSUES) ====================

    def get_issues(self, state: str = "opened", assignee: str | None = None) -> list[dict]:
        project = self.get_project()
        params = {"state": state}
        if assignee == "me":
            self.gl.auth()
            params["assignee_id"] = self.gl.user.id

        issues = project.issues.list(**params, all=True)

        return [
            {
                "iid": issue.iid,
                "title": issue.title,
                "description": issue.description,
                "state": issue.state,
                "labels": issue.labels,
                "assignee": issue.assignee["username"] if issue.assignee else None,
                "created_at": issue.created_at,
                "due_date": issue.due_date, # <--- ДОБАВИЛИ ВОТ ЭТО
                "web_url": issue.web_url,
            }
            for issue in issues
        ]

    def get_issue(self, issue_iid: int) -> dict:
        project = self.get_project()
        issue = project.issues.get(issue_iid)
        return {
            "iid": issue.iid,
            "title": issue.title,
            "description": issue.description,
            "state": issue.state,
            "labels": issue.labels,
            "assignee": issue.assignee["username"] if issue.assignee else None,
            "created_at": issue.created_at,
            "due_date": issue.due_date, # <--- И ЗДЕСЬ
            "web_url": issue.web_url,
        }

    def create_issue(self, title: str, description: str = "", labels: list[str] | None = None) -> dict:
        """Создаёт новую задачу"""
        project = self.get_project()
        issue = project.issues.create({
            "title": title,
            "description": description,
            "labels": labels or [],
        })

        return {
            "iid": issue.iid,
            "title": issue.title,
            "web_url": issue.web_url,
        }

    # ==================== РАБОТА С MERGE REQUESTS ====================

    def create_merge_request(
        self,
        source_branch: str,
        title: str,
        description: str = "",
        target_branch: str | None = None,
    ) -> dict:
        """Создаёт Merge Request"""
        project = self.get_project()
        target = target_branch or self.default_branch

        mr = project.mergerequests.create({
            "source_branch": source_branch,
            "target_branch": target,
            "title": title,
            "description": description,
            "remove_source_branch": True,
        })

        return {
            "iid": mr.iid,
            "title": mr.title,
            "web_url": mr.web_url,
            "state": mr.state,
        }


# Глобальный экземпляр
gitlab_client = GitLabAdapter()