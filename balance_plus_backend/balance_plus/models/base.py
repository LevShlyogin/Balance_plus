from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from uuid import UUID
from datetime import datetime

class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass

# Опционально: можно определить общие колонки здесь,
# но для чистоты оставим их в каждой модели.
# class TimestampedBase(Base):
#     __abstract__ = True
#     created_at: Mapped[datetime] = mapped_column(server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now()) 