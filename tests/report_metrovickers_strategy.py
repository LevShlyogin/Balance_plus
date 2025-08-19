import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metrovickers_strategy import MetroVickersStrategy

def main():
    strategy = MetroVickersStrategy()

    input_params = {
        'diameter_inside_of_pipes': 20, # Внутренний диаметр трубок (мм)
        'thickness_pipe_wall': 0.0, # Толщина стенки трубок
        'length_cooling_tubes_of_the_main_bundle': 7.08, # Активная длина охл. труб
        'number_cooling_tubes_of_the_main_bundle': 1754, # Количество трубок полное (шт.)
        'number_cooling_tubes_of_the_built_in_bundle': 418, # Количество трубок воздухоохладителя (шт.)
        'number_cooling_water_passes_of_the_main_bundle': 2, # Число ходов охлаждающей воды Z
        'mass_flow_cooling_water': 1200.0, # Расход охлаждающей воды (м3/час)
        'temperature_cooling_water_1': 35.0, # Ср. температура охлажд. воды (°C)
        'thermal_conductivity_cooling_surface_tube_material': 37.0, # Коэф-нт теплопровод. матер. трубок (ккал/м*час*°С)
        'coefficient_b': 0.974, # Коэф-нт влияния Dтруб на теор. коэф-нт теплопередачи, B
        'mass_flow_flow_path_1': 100.0, 
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