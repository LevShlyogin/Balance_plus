FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry==1.7.1

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock* ./

# Установка зависимостей
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копирование кода приложения
COPY app ./app
COPY tests ./tests

# Создание рабочих директорий
RUN mkdir -p /tmp/condenser_repos

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
ENV CELERY_RESULT_BACKEND=rpc://

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A app inspect ping -d celery@$HOSTNAME || exit 1

# Команда запуска
CMD ["celery", "-A", "app", "worker", "--loglevel=info", "--concurrency=2", "-Q", "condenser_calculation_queue"]