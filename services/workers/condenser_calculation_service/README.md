# Condenser Calculation Microservice

## 📋 Описание

Микросервис для выполнения теплогидравлических расчётов конденсаторов паровых турбин по методикам:
- **Berman** (С.С. Берман)
- **Metro-Vickers**
- **VKU** (Воздушно-конденсационная установка)
- **Table Pressure** (Табличный метод)

### Ключевые особенности

✅ **Reproducible Snapshot (v1.2)** — полная воспроизводимость расчётов с трассировкой источников данных  
✅ **Git-based provenance** — каждый расчёт привязан к конкретным commit_hash  
✅ **Pydantic V2 validation** — строгая валидация входных и выходных данных  
✅ **Celery-based architecture** — асинхронная обработка задач  
✅ **Docker-ready** — контейнеризация для простого развёртывания  

---

## 📁 Структура проекта

```
condenser_calculation_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── settings.py
│   ├── schemas.py
│   ├── calculator/
│   │   ├── __init__.py
│   │   ├── berman.py
│   │   ├── metro_vickers.py
│   │   ├── vku.py
│   │   └── table_pressure.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── condenser_task.py
│   └── utils/
│       ├── __init__.py
│       ├── io.py
│       ├── validation.py
│       ├── constants.py
│       └── uniconv.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_schemas.py
│   ├── test_io.py
│   ├── test_validation.py
│   ├── test_berman_strategy.py
│   ├── test_metro_vickers_strategy.py
│   ├── test_vku_strategy.py
│   └── test_condenser_task.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── api.js
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .gitlab-ci.yml
├── pyproject.toml
├── README.md
└── .env.example
```

---

## 🏗️ Архитектура

```
Frontend IDE → Orchestrator → RabbitMQ → Condenser Worker → Git
                                            ↓
                                       Calculation
                                       (Berman/MV/VKU)
                                            ↓
                                       Results JSON
```

---

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Docker & Docker Compose
- Git

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://gitlab.example.com/balanceplus/condenser-service.git
cd condenser-service

# Установка зависимостей
poetry install

# Запуск тестов
poetry run pytest

# Запуск через Docker Compose
cd docker
docker-compose up -d
```

### Проверка работоспособности

```bash
# Проверка статуса worker
docker-compose exec worker celery -A app inspect ping

# Открыть Flower (мониторинг Celery)
open http://localhost:5555
```

---

## 📁 Структура JSON-контрактов (v1.2)

### Входной файл: `condenser_input.json`

```json
{
  "schema_version": "1.2",
  "_meta": {
    "target_project_path": "project-a"
  },
  "geometry_source": {
    "type": "reference",
    "source_info": {
      "project_path": "project-a",
      "commit_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    },
    "path": "geometries/condensers/K-300-240-LMZ.json"
  },
  "parameters_source": {
    "type": "reference",
    "source_info": {
      "project_path": "project-b-reference",
      "commit_hash": "e6f7g8h9j0k1e6f7g8h9j0k1e6f7g8h9j0k1e6f7"
    },
    "path": "path/to/reference_parameters.json"
  },
  "calculation_strategy": "berman",
  "parameters": {
    "mass_flow_steam_list": [850.0, 800.0, 750.0],
    "enthalpy_flow_path_1": 2300.5,
    "mass_flow_cooling_water_list": [40000, 42000, 44000],
    "temperature_cooling_water_1_list": [15.0, 16.0, 17.0],
    "coefficient_R_list": [0.0001, 0.00015, 0.0002]
  }
}
```

### Выходной файл: `condenser_results.json`

```json
{
  "schema_version": "1.2",
  "input_commit_hash": "c4d5e6f...",
  "calculation_strategy": "berman",
  "_meta": {
    "target_project": {
      "path": "project-a",
      "attributes": {}
    },
    "sources": {
      "geometry": {
        "project_path": "project-a",
        "commit_hash": "a1b2c3d4...",
        "path": "geometries/condensers/K-300-240-LMZ.json"
      },
      "parameters": {
        "project_path": "project-b-reference",
        "commit_hash": "e6f7g8h9...",
        "path": "path/to/reference_parameters.json"
      }
    }
  },
  "results": {
    "berman_results": {
      "main_results": [
        {
          "condenser_pressure_Pa": 4500.0,
          "saturation_temperature_C": 30.5,
          "undercooling_main_bundle_C": 2.3,
          "undercooling_built_in_bundle_C": 0.0
        }
      ],
      "ejector_results": []
    }
  }
}
```

---

## 🧪 Тестирование

```bash
# Все тесты
poetry run pytest

# С покрытием кода
poetry run pytest --cov=app --cov-report=html

# Только unit-тесты
poetry run pytest tests/test_berman_strategy.py -v

# Только интеграционные тесты
poetry run pytest tests/test_condenser_task.py -v
```

---

## 📊 Мониторинг

### Flower Dashboard

```bash
open http://localhost:5555
```

### Логи

```bash
# Логи worker
docker-compose logs -f worker

# Логи RabbitMQ
docker-compose logs -f rabbitmq
```

---

## 🔧 Конфигурация

Все параметры настраиваются через переменные окружения (см. `.env.example`):

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|----------------------|
| `CELERY_BROKER_URL` | URL брокера сообщений | `amqp://guest:guest@rabbitmq:5672//` |
| `CELERY_RESULT_BACKEND` | Backend для результатов | `redis://redis:6379/0` |
| `GIT_REPO_BASE_PATH` | Путь для клонирования репозиториев | `/tmp/condenser_repos` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

---

## 🛠️ Разработка

### Добавление новой стратегии расчёта

1. Создать класс в `app/calculator/my_strategy.py`:

```python
class MyStrategy:
    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Ваша логика
        return {"result": 42}
```

2. Добавить в `app/tasks/condenser_task.py`:

```python
elif strategy == "my_strategy":
    results = MyStrategy().calculate(params)
    results_wrapped = {"my_strategy_results": results}
```

3. Обновить схему в `app/schemas.py`:

```python
calculation_strategy: Literal["berman", "metro_vickers", "vku", "table_pressure", "my_strategy"]
```

4. Добавить валидацию в `app/utils/validation.py`

5. Написать тесты в `tests/test_my_strategy.py`

---

## 📝 Changelog

### v1.2.0 (2024-05-25)
- ✨ Поддержка JSON Schema v1.2 (Reproducible Snapshot)
- ✨ Обязательные `commit_hash` во всех `source_info`
- ✨ Полная трассировка источников данных в `_meta.sources`
- 🔒 Строгая валидация с `extra="forbid"`
- 📚 Обновлённая документация

### v1.1.0
- Добавлена стратегия VKU
- Улучшена обработка ошибок

### v1.0.0
- Первый релиз
- Поддержка стратегий Berman и Metro-Vickers

---

## 📄 Лицензия

Proprietary - Balance+ Platform

---

## 👥 Команда

- **Solutions Architect**: @architect
- **Backend Lead**: @backend-lead
- **DevOps**: @devops

---

## 📞 Поддержка

- **Issues**: https://gitlab.example.com/balanceplus/condenser-service/issues
- **Wiki**: https://wiki.balanceplus.example/condenser-service
- **Email**: support@balanceplus.example