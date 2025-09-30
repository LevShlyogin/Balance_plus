import pytest
from pydantic import ValidationError
from app.schemas import CalculationInputV1_2, CalculationResultsV1_2


def test_input_schema_valid(sample_input_berman_v1_2):
    """Тест валидации корректного входного файла"""
    model = CalculationInputV1_2.model_validate(sample_input_berman_v1_2)
    assert model.schema_version == "1.2"
    assert model.calculation_strategy == "berman"
    assert model.meta.target_project_path == "project-a"


def test_input_schema_invalid_version():
    """Тест отклонения неверной версии схемы"""
    invalid_data = {
        "schema_version": "1.0",  # Неверная версия
        "_meta": {"target_project_path": "project-a"},
        "geometry_source": {
            "type": "reference",
            "source_info": {"project_path": "project-a", "commit_hash": "abc123"},
            "path": "geometry.json"
        },
        "parameters_source": {
            "type": "reference",
            "source_info": {"project_path": "project-a", "commit_hash": "abc123"}
        },
        "calculation_strategy": "berman",
        "parameters": {}
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CalculationInputV1_2.model_validate(invalid_data)
    
    assert "schema_version" in str(exc_info.value)


def test_input_schema_missing_commit_hash():
    """Тест отклонения данных без commit_hash"""
    invalid_data = {
        "schema_version": "1.2",
        "_meta": {"target_project_path": "project-a"},
        "geometry_source": {
            "type": "reference",
            "source_info": {"project_path": "project-a"},  # Отсутствует commit_hash
            "path": "geometry.json"
        },
        "parameters_source": {
            "type": "reference",
            "source_info": {"project_path": "project-a", "commit_hash": "abc123"}
        },
        "calculation_strategy": "berman",
        "parameters": {}
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CalculationInputV1_2.model_validate(invalid_data)
    
    assert "commit_hash" in str(exc_info.value)


def test_output_schema_valid():
    """Тест валидации корректного выходного файла"""
    output_data = {
        "schema_version": "1.2",
        "input_commit_hash": "c4d5e6f7",
        "calculation_strategy": "berman",
        "_meta": {
            "target_project": {
                "path": "project-a",
                "attributes": {}
            },
            "sources": {
                "geometry": {
                    "project_path": "project-a",
                    "commit_hash": "a1b2c3d4",
                    "path": "geometry.json"
                },
                "parameters": {
                    "project_path": "project-b",
                    "commit_hash": "e6f7g8h9",
                    "path": "params.json"
                }
            }
        },
        "results": {
            "berman_results": {
                "main_results": [],
                "ejector_results": []
            }
        }
    }
    
    model = CalculationResultsV1_2.model_validate(output_data)
    assert model.schema_version == "1.2"
    assert model.input_commit_hash == "c4d5e6f7"
    assert model.meta.sources.geometry.commit_hash == "a1b2c3d4"


def test_output_schema_extra_fields_forbidden():
    """Тест что дополнительные поля запрещены"""
    output_data = {
        "schema_version": "1.2",
        "input_commit_hash": "c4d5e6f7",
        "calculation_strategy": "berman",
        "extra_field": "should_fail",  # Лишнее поле
        "_meta": {
            "target_project": {"path": "project-a", "attributes": {}},
            "sources": {
                "geometry": {"project_path": "project-a", "commit_hash": "a1b2c3d4"},
                "parameters": {"project_path": "project-b", "commit_hash": "e6f7g8h9"}
            }
        },
        "results": {}
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CalculationResultsV1_2.model_validate(output_data)
    
    assert "extra_field" in str(exc_info.value)
