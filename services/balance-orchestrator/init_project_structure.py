# init_project_structure.py
"""
Инициализация структуры проекта Balance+ в GitLab.
Создаёт базовые папки и файлы-манифесты.
"""
import json
from datetime import datetime
from gitlab_adapter import gitlab_client


def create_project_structure():
    """Создаёт начальную структуру проекта для расчётов Balance+"""

    print("=== Инициализация структуры проекта Balance+ ===\n")

    # 1. Манифест проекта — описывает структуру и метаданные
    project_manifest = {
        "schema_version": "1.0",
        "project_type": "balance_calculation",
        "created_at": datetime.now().isoformat(),
        "created_by": "balance-plus-orchestrator",
        "description": "Тестовый проект для проверки системы Balance+",
        "structure": {
            "inputs": "Входные данные для расчётов",
            "outputs": "Результаты расчётов",
            "geometries": "Геометрические модели",
            "configs": "Конфигурационные файлы",
        },
    }

    # 2. Манифест геометрий — список доступных геометрий
    geometries_manifest = {
        "schema_version": "1.0",
        "geometries": [
            {
                "id": "geometry_001",
                "name": "Базовая геометрия конденсатора",
                "file": "geometries/condenser_base.json",
                "type": "condenser",
                "description": "Стандартная геометрия для расчёта конденсатора",
            },
            {
                "id": "geometry_002",
                "name": "Геометрия штоков тип А",
                "file": "geometries/rods_type_a.json",
                "type": "rods",
                "description": "Геометрия штоков типа А",
            },
        ],
    }

    # 3. Шаблон входных данных для расчёта баланса
    balance_input_template = {
        "schema_version": "1.0",
        "calculation_type": "balance",
        "metadata": {
            "task_id": None,
            "created_at": None,
            "author": None,
        },
        "parameters": {
            "temperature": {"value": None, "unit": "°C", "description": "Температура среды"},
            "pressure": {"value": None, "unit": "МПа", "description": "Давление"},
            "flow_rate": {"value": None, "unit": "кг/с", "description": "Расход"},
        },
        "geometry_ref": None,
    }

    # 4. Шаблон входных данных для расчёта конденсатора
    condenser_input_template = {
        "schema_version": "1.0",
        "calculation_type": "condenser",
        "metadata": {
            "task_id": None,
            "created_at": None,
            "author": None,
        },
        "parameters": {
            "inlet_temperature": {"value": None, "unit": "°C"},
            "outlet_temperature": {"value": None, "unit": "°C"},
            "heat_transfer_coefficient": {"value": None, "unit": "Вт/(м²·К)"},
        },
        "geometry_ref": None,
    }

    # 5. Пример геометрии конденсатора
    condenser_geometry = {
        "id": "geometry_001",
        "type": "condenser",
        "version": "1.0",
        "dimensions": {
            "length": {"value": 2.5, "unit": "м"},
            "diameter": {"value": 0.8, "unit": "м"},
            "tube_count": 150,
            "tube_diameter": {"value": 0.025, "unit": "м"},
        },
        "materials": {
            "shell": "Сталь 12Х18Н10Т",
            "tubes": "Латунь Л68",
        },
    }

    # Список файлов для создания
    files_to_create = [
        ("balance_plus_manifest.json", project_manifest, "Манифест проекта"),
        ("geometries/geometries_manifest.json", geometries_manifest, "Манифест геометрий"),
        ("templates/balance_input_template.json", balance_input_template, "Шаблон входных данных баланса"),
        ("templates/condenser_input_template.json", condenser_input_template, "Шаблон входных данных конденсатора"),
        ("geometries/condenser_base.json", condenser_geometry, "Геометрия конденсатора"),
        ("inputs/.gitkeep", "", "Папка для входных данных"),
        ("outputs/.gitkeep", "", "Папка для результатов"),
        ("configs/.gitkeep", "", "Папка для конфигов"),
    ]

    # Создаём файлы
    for file_path, content, description in files_to_create:
        print(f"📄 Создаём: {file_path} — {description}")

        # Преобразуем в JSON если это словарь
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_str = content

        try:
            commit = gitlab_client.create_commit(
                file_path=file_path,
                content=content_str,
                commit_message=f"Init: {description}",
            )
            print(f"   ✅ Коммит: {commit.short_id}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

    print("\n=== Структура проекта создана! ===")
    print("Теперь можно открыть проект в GitLab и увидеть все файлы.")


if __name__ == "__main__":
    create_project_structure()