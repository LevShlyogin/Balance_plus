import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metrovickers_strategy import MetroVickersStrategy

def main():
    strategy = MetroVickersStrategy()

    input_params = {
        'diameter_inside_of_pipes': 21.0,
        'thickness_pipe_wall': 1.5,
        'length_cooling_tubes_of_the_main_bundle': 8000.0,
        'number_cooling_tubes_of_the_main_bundle': 6000,
        'number_cooling_tubes_of_the_built_in_bundle': 500,
        'number_cooling_water_passes_of_the_main_bundle': 2,
        'mass_flow_cooling_water': 12000.0,
        'temperature_cooling_water_1': 20.0,
        'thermal_conductivity_cooling_surface_tube_material': 55.0,
        'coefficient_b': 0.9,
        'mass_flow_flow_path_1': 250.0,
        'degree_dryness_flow_path_1': 0.92,
    }

    print("--- Входные параметры ---")
    print(json.dumps(input_params, indent=4))
    
    try:
        results = strategy.calculate(input_params)
        print("\n--- Результаты расчета ---")
        print(json.dumps(results, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"\n--- Ошибка при расчете ---")
        print(e)


if __name__ == '__main__':
    main()