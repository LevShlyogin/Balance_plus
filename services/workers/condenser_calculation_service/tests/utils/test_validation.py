import pytest
from app.utils.validation import validate_strategy_parameters


def test_validate_berman_success(sample_geometry_v1_2):
    """Тест успешной валидации для стратегии Berman"""
    params = {
        **sample_geometry_v1_2,
        "mass_flow_steam_list": [850.0],
        "temperature_cooling_water_1_list": [15.0],
        "mass_flow_cooling_water_list": [40000],
        "coefficient_R_list": [0.0001],
        "enthalpy_flow_path_1": 2300.5
    }
    
    # Не должно выбросить исключение
    validate_strategy_parameters(params, "berman")


def test_validate_berman_missing_fields(sample_geometry_v1_2):
    """Тест ошибки при отсутствии обязательных полей"""
    params = {**sample_geometry_v1_2}
    # Отсутствуют параметры режима
    
    with pytest.raises(ValueError, match="Missing required parameters"):
        validate_strategy_parameters(params, "berman")


def test_validate_metro_vickers_success(sample_geometry_v1_2):
    """Тест успешной валидации для Metro-Vickers"""
    params = {
        **sample_geometry_v1_2,
        "mass_flow_cooling_water": 41000,
        "temperature_cooling_water_1": 15.5,
        "mass_flow_flow_path_1": 850.0,
        "degree_dryness_flow_path_1": 0.95
    }
    
    validate_strategy_parameters(params, "metro_vickers")


def test_validate_unknown_strategy():
    """Тест ошибки для неизвестной стратегии"""
    with pytest.raises(ValueError, match="Unknown calculation strategy"):
        validate_strategy_parameters({}, "unknown_strategy")


def test_validate_vku_success():
    """Тест валидации для VKU стратегии"""
    params = {
        "mass_flow_flow_path_1": 850.0,
        "degree_dryness_flow_path_1": 0.95,
        "mass_flow_steam_nom": 900.0,
        "degree_dryness_steam_nom": 1.0
    }
    
    validate_strategy_parameters(params, "vku")