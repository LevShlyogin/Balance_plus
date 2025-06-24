import gitlab
from gitlab.v4.objects import Project, ProjectIssue, ProjectBranch

class GitLabService:
    def __init__(self, gitlab_url: str, private_token: str):
        self.gl = gitlab.Gitlab(gitlab_url, oauth_token=private_token)
        self.gl.auth()

    def get_current_user(self):
        """Возвращает аутентифицированного пользователя GitLab."""
        return self.gl.user

    def create_project_repo(self, name: str, template_project_id: int) -> Project:
        """Создает репозиторий в GitLab как форк шаблона."""
        template_project = self.gl.projects.get(template_project_id)
        project = template_project.fork(data={'name': name, 'path': name.lower().replace(' ', '-')})
        return project

    def create_issue(self, gitlab_project_id: int, title: str, assignee_id: int) -> ProjectIssue:
        """Создает Issue в проекте GitLab."""
        project = self.gl.projects.get(gitlab_project_id)
        issue = project.issues.create({'title': title, 'assignee_ids': [assignee_id]})
        return issue

    def create_branch(self, gitlab_project_id: int, branch_name: str, source_branch: str = 'main') -> ProjectBranch:
        """Создает ветку в репозитории GitLab."""
        project = self.gl.projects.get(gitlab_project_id)
        branch = project.branches.create({'branch': branch_name, 'ref': source_branch})
        return branch 