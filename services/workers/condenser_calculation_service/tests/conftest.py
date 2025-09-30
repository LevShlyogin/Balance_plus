import pytest
import json
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_geometry_v1_2() -> Dict[str, Any]:
    """Пример геометрии конденсатора"""
    return {
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


@pytest.fixture
def sample_input_berman_v1_2() -> Dict[str, Any]:
    """Пример входного файла для стратегии Berman"""
    return {
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


@pytest.fixture
def sample_input_metro_vickers_v1_2() -> Dict[str, Any]:
    """Пример входного файла для стратегии Metro-Vickers"""
    return {
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
                "project_path": "project-a",
                "commit_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
            },
            "path": "parameters/metro_vickers_params.json"
        },
        "calculation_strategy": "metro_vickers",
        "parameters": {
            "mass_flow_cooling_water": 41000,
            "temperature_cooling_water_1": 15.5,
            "coefficient_b": 1.0,
            "mass_flow_flow_path_1": 850.0,
            "degree_dryness_flow_path_1": 0.95
        }
    }


@pytest.fixture
def temp_work_dir(tmp_path):
    """Создаёт временную рабочую директорию"""
    work_dir = tmp_path / "condenser_work"
    work_dir.mkdir()
    return work_dir