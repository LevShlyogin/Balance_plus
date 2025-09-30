import pytest
import json
from pathlib import Path
from app.utils.io import load_input_file, load_geometry_data, save_results_file


def test_load_input_file_success(temp_work_dir, sample_input_berman_v1_2):
    """Тест успешной загрузки входного файла"""
    input_path = temp_work_dir / "input.json"
    input_path.write_text(json.dumps(sample_input_berman_v1_2, ensure_ascii=False))
    
    data = load_input_file(str(input_path))
    assert data["schema_version"] == "1.2"
    assert data["calculation_strategy"] == "berman"


def test_load_input_file_not_found(temp_work_dir):
    """Тест ошибки при отсутствии файла"""
    with pytest.raises(FileNotFoundError):
        load_input_file(str(temp_work_dir / "nonexistent.json"))


def test_load_geometry_data_success(temp_work_dir, sample_geometry_v1_2):
    """Тест успешной загрузки геометрии"""
    geometry_path = temp_work_dir / "geometry.json"
    geometry_path.write_text(json.dumps(sample_geometry_v1_2, ensure_ascii=False))
    
    data = load_geometry_data(str(geometry_path))
    assert data["schema_version"] == "1.0"
    assert data["name"] == "Конденсатор турбины К-300-240"


def test_load_geometry_data_missing_version(temp_work_dir):
    """Тест ошибки при отсутствии schema_version"""
    geometry_path = temp_work_dir / "geometry.json"
    geometry_path.write_text(json.dumps({"name": "Test"}))
    
    with pytest.raises(ValueError, match="schema_version"):
        load_geometry_data(str(geometry_path))


def test_save_results_file(temp_work_dir):
    """Тест успешного сохранения результатов"""
    output_data = {
        "schema_version": "1.2",
        "input_commit_hash": "abc123",
        "calculation_strategy": "berman",
        "_meta": {
            "target_project": {"path": "project-a", "attributes": {}},
            "sources": {
                "geometry": {"project_path": "project-a", "commit_hash": "def456"},
                "parameters": {"project_path": "project-a", "commit_hash": "ghi789"}
            }
        },
        "results": {"berman_results": {"main_results": []}}
    }
    
    output_path = temp_work_dir / "output" / "results.json"
    save_results_file(output_data, str(output_path))
    
    assert output_path.exists()
    saved_data = json.loads(output_path.read_text())
    assert saved_data["schema_version"] == "1.2"