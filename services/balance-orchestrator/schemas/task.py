# schemas/task.py
from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime, date


# Словарь: "Русское название в GitLab" -> "Системный код для вкладок"
TYPE_MAPPING = {
    "Штоки клапанов": "valves",
    "valves": "valves",
    "Балансы": "balance",
    "Треугольники скоростей": "triangles",
    "Тепловые расчёты": "thermal",
    "Прочность": "strength",
    "Вибрация": "vibration"
}

class TaskInfo(BaseModel):
    iid: int
    title: str
    description: Optional[str] = None
    state: str
    labels: list[str] = []
    assignee: Optional[str] = None
    created_at: datetime
    due_date: Optional[date] = None
    web_url: str

    @computed_field
    def formatted_date(self) -> str:
        return self.created_at.strftime("%d.%m.%y")

    @computed_field
    def calc_type(self) -> str:
        """
        Ищем тег, который есть в нашем словаре типов.
        Возвращаем системный код (например, 'thermal').
        """
        for label in self.labels:
            if label in TYPE_MAPPING:
                return TYPE_MAPPING[label]
        return "general" # Если специфичного тега нет

    @computed_field
    def calc_type_human(self) -> str:
        """
        Возвращаем человеческое название для отображения на карточке (например, 'Тепловые расчёты')
        """
        for label in self.labels:
            if label in TYPE_MAPPING:
                return label
        return "Общая задача"

    @computed_field
    def turbine_project(self) -> str:
        """
        Всё, что НЕ является типом расчёта — считаем проектом/турбиной.
        Берем первый подходящий тег.
        """
        for label in self.labels:
            if label not in TYPE_MAPPING:
                return label
        return "Без проекта"
    
    @computed_field
    def status_rus(self) -> str:
        return "В работе" if self.state == "opened" else "Завершено"


class TaskCreate(BaseModel):
    """Данные для создания задачи"""
    title: str
    description: str = ""
    labels: list[str] = []


class BranchCreate(BaseModel):
    """Данные для создания ветки задачи"""
    issue_iid: int


class BranchInfo(BaseModel):
    """Информация о созданной ветке"""
    branch_name: str
    issue_iid: int
    created: bool
    