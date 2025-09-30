import json
from pathlib import Path
from typing import Dict, Any

from app.schemas import CalculationInputV1_2


def load_input_file(file_path: str) -> Dict[str, Any]:
    """
    Загружает и валидирует condenser_input.json по схеме 1.2.
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with file.open(encoding="utf-8") as f:
        data = json.load(f)
    
    # Валидация Pydantic
    CalculationInputV1_2.model_validate(data)
    
    return data


def load_geometry_data(file_path: str) -> Dict[str, Any]:
    """
    Загружает condenser_geometry.json в виде словаря.
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Geometry file not found: {file_path}")
    
    with file.open(encoding="utf-8") as f:
        data = json.load(f)
    
    if "schema_version" not in data:
        raise ValueError("Geometry file missing 'schema_version' field")
    
    return data


def save_results_file(output_data: Dict[str, Any], output_path: str) -> None:
    """
    Сохраняет результирующий condenser_results.json.
    """
    file = Path(output_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    
    with file.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)