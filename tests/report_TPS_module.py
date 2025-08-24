from pprint import pprint
from utils.TPS_module import TablePressureStrategy

params_1 = {
    'temperature_cooling_water_1': 27.0,
    'mass_flow_flow_path_1': 112.0,
    
    'NAMET': [
        [35, 33, 30, 25],
        [20, 50, 100, 150, 200],
        [
            [6.549, 7.211, 8.88, 10.945, 13.409],
            [5.9, 6.499, 8.018, 9.927, 12.214],
            [5.036, 5.552, 6.872, 8.572, 10.622],
            [3.851, 4.257, 5.299, 6.712, 8.438]
        ]
    ],
    'NAMED': [
        [20, 30, 40],
        [0.1, 0.2, 0.3] 
    ]
}

params_2 = {
    'temperature_cooling_water_1': 30.0,
    'mass_flow_flow_path_1': 150.0,
    
    'NAMET': [
        [10, 20, 30],
        [100, 200, 300],
        [
            [0.1, 0.1, 0.1], 
            [0.1, 0.1, 0.1], 
            [0.1, 0.1, 0.1]
        ]
    ],
    'NAMED': [
        [15.3, 26.8, 38.4, 49.9, 61.5, 73],
        [0.157, 0.258, 0.469, 0.607, 0.763, 0.919]
    ]
}


if __name__ == "__main__":
    strategy = TablePressureStrategy()

    print("="*20 + " Кейс 1 " + "="*20)
    print("Входные параметры:")
    pprint(params_1)
    
    results_1 = strategy.calculate(params_1)
    
    print("\nРезультаты расчета:")
    pprint(results_1)
    print(f"\nОжидаемый результат P1 = 7.758")
    print(f"Полученный результат P1 = {results_1['pressure_flow_path_1']:.3f}\n")

    print("="*20 + " Кейс 2 " + "="*20)
    print("Входные параметры:")
    pprint(params_2)

    results_2 = strategy.calculate(params_2)

    print("\nРезультаты расчета:")
    pprint(results_2)
    print(f"\nОжидаемый результат P1 = 0.316")
    print(f"Полученный результат P1 = {results_2['pressure_flow_path_1']:.3f}")