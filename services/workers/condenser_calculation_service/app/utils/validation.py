from typing import Dict, List


def validate_strategy_parameters(params: Dict, strategy: str):
    """
    Проверяет наличие обязательных параметров для выбранной стратегии.
    """
    required_fields: Dict[str, List[str]] = {
        "berman": [
            "diameter_inside_of_pipes",
            "thickness_pipe_wall",
            "number_cooling_tubes_of_the_main_bundle",
            "length_cooling_tubes_of_the_main_bundle",
            "number_cooling_water_passes_of_the_main_bundle",
            "mass_flow_steam_nom",
            "enthalpy_flow_path_1",
            "mass_flow_steam_list",
            "temperature_cooling_water_1_list",
            "mass_flow_cooling_water_list",
            "coefficient_R_list",
            "thermal_conductivity_cooling_surface_tube_material"
        ],
        "metro_vickers": [
            "diameter_inside_of_pipes",
            "thickness_pipe_wall",
            "length_cooling_tubes_of_the_main_bundle",
            "number_cooling_water_passes_of_the_main_bundle",
            "number_cooling_tubes_of_the_main_bundle",
            "number_cooling_tubes_of_the_built_in_bundle",
            "mass_flow_cooling_water",
            "temperature_cooling_water_1",
            "mass_flow_flow_path_1",
            "degree_dryness_flow_path_1",
            "thermal_conductivity_cooling_surface_tube_material"
        ],
        "vku": [
            "mass_flow_flow_path_1",
            "degree_dryness_flow_path_1",
            "mass_flow_steam_nom",
            "degree_dryness_steam_nom"
        ],
        "table_pressure": [
            "NAMET",
            "NAMED",
            "inputs"
        ]
    }
    
    if strategy not in required_fields:
        raise ValueError(f"Unknown calculation strategy: {strategy}")
    
    missing = [f for f in required_fields[strategy] if f not in params]
    
    if missing:
        raise ValueError(f"Missing required parameters for '{strategy}': {missing}")