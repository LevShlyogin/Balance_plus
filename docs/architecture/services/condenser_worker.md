# **Техническое Задание: Микросервис Расчёта Конденсатора**

**Версия:** 1.2.0  
**Дата:** 22.09.2025  
**Статус:** Утверждено  
**Владелец:** Команда Расчётных Модулей Balance+

---

## 1. Роль и ответственность

Микросервис Расчёта Конденсатора (`CondenserCalculationService`) является `Celery-worker`'ом, отвечающим **исключительно** за выполнение теплогидравлического расчёта режимов работы конденсатора по следующим методикам:

- **Berman** (С.С. Берман)
- **Metro-Vickers**
- **VKU** (Воздушно-конденсационная установка)
- **Table Pressure** (Табличный метод)

### Архитектурная роль

Сервис является **чистым, изолированным вычислительным компонентом** и:

- ✅ Не хранит состояние (`stateless`)
- ✅ Не имеет собственной базы данных
- ✅ Взаимодействует через **RabbitMQ** (получение задач) и **Git** (чтение/запись данных)
- ✅ Является конкретной реализацией [Шаблона Расчётного Микросервиса на базе Celery](./worker-template.md)

---

## 2. Ключевые компоненты (C4 Model - Level 3)

| Компонент | Описание | Статус |
|:----------|:---------|:-------|
| **Celery Consumer** | Стандартный компонент из шаблона. Получает задачи из `condenser_calculation_queue`, управляет жизненным циклом (включая retry) | ✅ Реализовано |
| **Validation Layer** | Pydantic V2 модели для строгой валидации входных/выходных данных по схеме v1.2 | ✅ Реализовано |
| **Git Handler** | Переиспользуемый компонент: `clone`, `checkout`, `commit`, `push` | ⚠️ Делегировано Оркестратору |
| **Ядро Расчёта** | Математическая логика: 4 стратегии расчёта, парсинг входных файлов, формирование результатов | ✅ Реализовано |

---

## 3. Функциональные требования и контракты

### 3.1. Celery-задача

**Параметры задачи:**

| Параметр | Тип | Описание |
|:---------|:----|:---------|
| `correlation_id` | `str` | Уникальный ID для трассировки |
| `repo_url` | `str` | URL Git-репозитория |
| `branch` | `str` | Ветка репозитория |
| `commit_hash` | `str` | Хеш коммита входных данных |
| `input_files` | `List[str]` | Список путей к входным файлам (обычно 1 файл) |
| `output_file` | `str` | Путь к выходному файлу результатов |

**Конфигурация:**

```python
@celery_app.task(
    bind=True, 
    name='calculation.condenser',
    queue='condenser_calculation_queue',
    max_retries=3,
    default_retry_delay=60
)
```

---

### 3.2. Контракт входных данных v1.2 (Reproducible Snapshot)

#### 3.2.1. Основной входной файл: `condenser_input.json`

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
    "coefficient_R_list": [0.0001, 0.00015, 0.0002],
    "mass_flow_air": 5.0,
    "BAP": 1
  }
}
```

**Обязательные поля:**

- `schema_version`: `"1.2"` (Literal)
- `_meta.target_project_path`: путь к целевому проекту
- `geometry_source.source_info.commit_hash`: **обязательный** для воспроизводимости
- `parameters_source.source_info.commit_hash`: **обязательный** для воспроизводимости
- `calculation_strategy`: одна из `["berman", "metro_vickers", "vku", "table_pressure"]`
- `parameters`: Dict с параметрами режима (зависят от стратегии)

#### 3.2.2. Файл геометрии: `condenser_geometry.json`

```json
{
  "schema_version": "1.0",
  "name": "Конденсатор турбины К-300-240",
  "type_condenser": "SIMPLE",
  "material_cooling_tubes": "МНЖ5-1",
  "thermal_conductivity_cooling_surface_tube_material": 45.0,
  "mass_flow_steam_nom": 850.0,
  "diameter_inside_of_pipes": 28.0,
  "thickness_pipe_wall": 1.0,
  "length_cooling_tubes_of_the_main_bundle": 9000.0,
  "number_cooling_tubes_of_the_main_bundle": 8000,
  "number_cooling_water_passes_of_the_main_bundle": 2,
  "length_cooling_tubes_of_the_built_in_bundle": 9000.0,
  "number_cooling_tubes_of_the_built_in_bundle": 1500,
  "number_cooling_water_passes_of_the_built_in_bundle": 2
}
```

---

### 3.3. Контракт выходных данных v1.2

**Файл:** `condenser_results.json`

```json
{
  "schema_version": "1.2",
  "input_commit_hash": "c4d5e6f7...",
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

**Ключевые особенности v1.2:**

- ✅ Полная трассировка источников в `_meta.sources`
- ✅ Обязательный `input_commit_hash`
- ✅ Копирование всех `commit_hash` из входных данных
- ✅ 100% воспроизводимость расчёта

---

### 3.4. Логика выполнения (C4 Model - Level 4: Code)

```python
@celery_app.task(bind=True, name='calculation.condenser')
def calculate_condenser(
    self, 
    correlation_id: str,
    repo_url: str, 
    branch: str, 
    commit_hash: str,
    input_files: List[str], 
    output_file: str
) -> str:
    try:
        # === 1. Загрузка и валидация входных данных ===
        input_data = load_input_file(input_files[0])
        model = CalculationInputV1_2.model_validate(input_data)  # Pydantic V2
        
        logger.info(f"[{correlation_id}] Strategy: {model.calculation_strategy}")
        
        # === 2. Загрузка геометрии ===
        if model.geometry_source.type == "reference":
            geometry_data = load_geometry_data(model.geometry_source.path)
        else:
            raise NotImplementedError("Inline geometry not supported in v1.2")
        
        # === 3. Объединение параметров ===
        params = {**geometry_data, **model.parameters}
        
        # === 4. Выбор и валидация стратегии ===
        validate_strategy_parameters(params, model.calculation_strategy)
        
        if model.calculation_strategy == "berman":
            results = BermanStrategy().calculate(params)
            results_wrapped = {"berman_results": results}
        elif model.calculation_strategy == "metro_vickers":
            results = MetroVickersStrategy().calculate(params)
            results_wrapped = {"metro_vickers_results": results}
        elif model.calculation_strategy == "vku":
            vku = VKUStrategy(
                mass_flow_steam_nom=params['mass_flow_steam_nom'],
                degree_dryness_steam_nom=params['degree_dryness_steam_nom']
            )
            results = vku.calculate(params)
            results_wrapped = {"vku_results": results}
        elif model.calculation_strategy == "table_pressure":
            results = TablePressureStrategy().calculate(params)
            results_wrapped = {"table_pressure_results": results}
        else:
            raise ValueError(f"Unknown strategy: {model.calculation_strategy}")
        
        logger.info(f"[{correlation_id}] Calculation completed")
        
        # === 5. Формирование выходного JSON ===
        output_model = CalculationResultsV1_2(
            schema_version="1.2",
            input_commit_hash=commit_hash,
            calculation_strategy=model.calculation_strategy,
            meta={
                "target_project": {
                    "path": model.meta.target_project_path,
                    "attributes": {}
                },
                "sources": {
                    "geometry": {
                        "project_path": model.geometry_source.source_info.project_path,
                        "commit_hash": model.geometry_source.source_info.commit_hash,
                        "path": model.geometry_source.path
                    },
                    "parameters": {
                        "project_path": model.parameters_source.source_info.project_path,
                        "commit_hash": model.parameters_source.source_info.commit_hash,
                        "path": model.parameters_source.path
                    }
                }
            },
            results=results_wrapped
        )
        
        # === 6. Сохранение ===
        save_results_file(output_model.model_dump(by_alias=True), output_file)
        logger.info(f"[{correlation_id}] Results saved to: {output_file}")
        
        return "SUCCESS"
        
    except FileNotFoundError as e:
        logger.error(f"[{correlation_id}] File not found: {e}")
        raise  # FAILED
    
    except ValueError as e:
        logger.error(f"[{correlation_id}] Validation error: {e}")
        raise  # FAILED
    
    except Exception as e:
        # Retry для инфраструктурных ошибок
        if "push" in str(e).lower() or "network" in str(e).lower():
            raise self.retry(exc=e, countdown=60, max_retries=3)
        raise
```

---

## 4. Параметры стратегий расчёта

### 4.1. Berman Strategy

**Обязательные параметры:**

| Параметр | Тип | Единицы | Описание |
|:---------|:----|:--------|:---------|
| `mass_flow_steam_list` | `List[float]` | т/ч | Расходы пара |
| `enthalpy_flow_path_1` | `float` | кДж/кг | Энтальпия пара |
| `mass_flow_cooling_water_list` | `List[float]` | т/ч | Расходы охлаждающей воды |
| `temperature_cooling_water_1_list` | `List[float]` | °C | Температуры входа воды |
| `coefficient_R_list` | `List[float]` | (м²·К)/Вт | Термическое сопротивление загрязнений |

### 4.2. Metro-Vickers Strategy

| Параметр | Тип | Единицы | Описание |
|:---------|:----|:--------|:---------|
| `mass_flow_cooling_water` | `float` | т/ч | Расход охлаждающей воды |
| `temperature_cooling_water_1` | `float` | °C | Температура входа воды |
| `coefficient_b` | `float` | - | Коэффициент чистоты (0-1) |
| `mass_flow_flow_path_1` | `float` | т/ч | Расход пара |
| `degree_dryness_flow_path_1` | `float` | - | Степень сухости пара (0-1) |

### 4.3. VKU Strategy

| Параметр | Тип | Единицы | Описание |
|:---------|:----|:--------|:---------|
| `mass_flow_flow_path_1` | `float` | т/ч | Расход пара |
| `degree_dryness_flow_path_1` | `float` | - | Степень сухости пара |
| `mass_flow_steam_nom` | `float` | т/ч | Номинальный расход пара |
| `degree_dryness_steam_nom` | `float` | - | Номинальная степень сухости |
| `temperature_air` | `float` (optional) | °C | Температура воздуха (по умолчанию: 20.0) |

### 4.4. Table Pressure Strategy

| Параметр | Тип | Описание |
|:---------|:----|:---------|
| `NAMET` | `Dict` | Табличные данные для интерполяции NAMET |
| `NAMED` | `Dict` | Табличные данные для интерполяции NAMED |
| `inputs` | `Dict` | Входные параметры для интерполяции |

---

## 5. Требования к тестированию

### 5.1. Unit-тесты (`pytest`)

**Покрытие:** Минимум 80%

#### 5.1.1. Тесты расчётных стратегий
#### 5.1.2. Тесты валидации (Pydantic)
#### 5.1.3. Тесты I/O утилит
#### 5.1.4. Тесты валидации параметров
### 5.2. Интеграционные тесты
### 5.3. Требования к покрытию

| Компонент | Минимальное покрытие | Статус |
|:----------|:--------------------|:-------|
| `app/schemas.py` | 95% | ✅ |
| `app/calculator/*.py` | 85% | ✅ |
| `app/utils/validation.py` | 100% | ✅ |
| `app/utils/io.py` | 90% | ✅ |
| `app/tasks/condenser_task.py` | 80% | ✅ |
| **Общее** | **80%** | ✅ |

---

## 6. Нефункциональные требования

### 6.1. Производительность

| Метрика | Требование | Измерение |
|:--------|:-----------|:----------|
| Время расчёта (Berman, 1 режим) | < 2 секунд | Per-task timer |
| Время расчёта (Metro-Vickers) | < 1 секунда | Per-task timer |
| Пропускная способность | > 100 задач/час | Flower monitoring |
| Использование памяти | < 512 MB на worker | Docker stats |

### 6.2. Надёжность

| Требование | Реализация |
|:-----------|:-----------|
| Автоматический retry при сетевых сбоях | `max_retries=3, countdown=60` |
| Graceful shutdown | Celery worker termination policy |
| Обработка всех исключений | Try-except блоки с логированием |
| Task timeout | `task_time_limit=3600, task_soft_time_limit=3300` |

### 6.3. Наблюдаемость

**Логирование:**
- Уровень: `INFO` (production), `DEBUG` (development)
- Формат: JSON structured logging
- Обязательные поля: `correlation_id`, `task_id`, `strategy`, `timestamp`

**Метрики (Prometheus):**
- `condenser_tasks_total{strategy, status}`
- `condenser_task_duration_seconds{strategy}`
- `condenser_calculation_errors_total{strategy, error_type}`

**Трассировка:**
- Все логи содержат `correlation_id` для end-to-end трейсинга

---

## 7. Технологический стек

| Компонент | Версия | Назначение |
|:----------|:-------|:-----------|
| **Python** | 3.10+ | Основной язык |
| **Celery** | 5.3.4+ | Task queue |
| **Pydantic** | 2.5.0+ | Валидация данных |
| **NumPy** | 1.26.0+ | Численные расчёты |
| **SciPy** | 1.11.0+ | Интерполяция |
| **seuif97** | 2.1.0+ (optional) | Свойства воды и пара |
| **pytest** | 7.4.3+ | Тестирование |
| **RabbitMQ** | 3.12+ | Message broker |
| **Redis** | 7+ | Result backend |
| **Docker** | 24+ | Контейнеризация |
