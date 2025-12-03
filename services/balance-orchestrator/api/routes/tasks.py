# api/routes/tasks.py
from fastapi import APIRouter, HTTPException
from slugify import slugify

from schemas.task import TaskInfo, TaskCreate, BranchCreate, BranchInfo
from gitlab_adapter import gitlab_client

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskInfo])
async def list_tasks(state: str = "opened", my_only: bool = False):
    """
    Получить список задач.
    - state: opened, closed, all
    - my_only: только мои задачи
    """
    try:
        assignee = "me" if my_only else None
        issues = gitlab_client.get_issues(state=state, assignee=assignee)
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения задач: {e}")


@router.get("/{issue_iid}", response_model=TaskInfo)
async def get_task(issue_iid: int):
    """Получить задачу по номеру"""
    try:
        issue = gitlab_client.get_issue(issue_iid)
        return issue
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Задача не найдена: {e}")


@router.post("", response_model=TaskInfo)
async def create_task(task: TaskCreate):
    """Создать новую задачу"""
    try:
        issue = gitlab_client.create_issue(
            title=task.title,
            description=task.description,
            labels=task.labels,
        )
        # Возвращаем полную информацию
        return gitlab_client.get_issue(issue["iid"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания задачи: {e}")


@router.post("/{issue_iid}/branch", response_model=BranchInfo)
async def create_task_branch(issue_iid: int):
    """
    Создать ветку для работы над задачей.
    Имя ветки: issue/{iid}-{transliterated-slug}
    """
    try:
        # Получаем информацию о задаче
        issue = gitlab_client.get_issue(issue_iid)

        # 1. Генерируем безопасный slug (кириллица -> латиница, пробелы -> дефисы)
        # Пример: "Тестовый расчёт" -> "testovyi-raschet"
        safe_slug = slugify(issue["title"], max_length=40)
        
        # Если заголовок был из одних спецсимволов, slug может быть пустым
        if not safe_slug:
            safe_slug = "task"

        branch_name = f"issue/{issue_iid}-{safe_slug}"

        print(f"🛠 Пытаемся создать ветку: {branch_name}") # Лог для отладки

        # Создаём ветку
        created = gitlab_client.create_branch(branch_name)

        return BranchInfo(
            branch_name=branch_name,
            issue_iid=issue_iid,
            created=created,
        )
    except Exception as e:
        # Логируем ошибку подробнее
        print(f"❌ Ошибка создания ветки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания ветки: {e}")