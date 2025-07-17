import unittest
from utils.berman_strategy import BermanStrategy

class TestBermanEjector(unittest.TestCase):
    def setUp(self):
        self.strategy = BermanStrategy()
        self.test_params = {
            'length_cooling_tubes_of_the_main_bundle': 7.080,
            'number_cooling_water_passes_of_the_main_bundle': 2,
            'number_cooling_tubes_of_the_main_bundle': 1754,
            'mass_flow_steam_nom': 16.0,
            'thermal_conductivity_cooling_surface_tube_material': 37.0,
            'diameter_inside_of_pipes': 22.0,
            'thickness_pipe_wall': 1.0,
            'enthalpy_flow_path_1': 520.0,
            'BAP': 1,
            'mass_flow_cooling_water_list': [1200],
            'temperature_cooling_water_1_list': [4, 5, 10, 15, 20, 25, 30, 35],
            'mass_flow_steam_list': [16],
            'coefficient_R_list': [0.10e-6],
            'mass_flow_air': 16.5,
            'number_ejector': 1,
        }

    def test_ejector_pressure_values(self):
        results = self.strategy.calculate(self.test_params)
        all_ejector_results = results['ejector_results']

        self.assertIsNotNone(all_ejector_results, "Результаты по эжектору отсутствуют.")
        
        ejector_results_for_one = [
            item for item in all_ejector_results if item['number_of_ejectors'] == 1
        ]
        
        self.assertEqual(len(ejector_results_for_one), len(self.test_params['temperature_cooling_water_1_list']),
                         "Количество результатов для одного эжектора не совпадает с количеством температур.")

        ejector_pressure_map = {
            item['inlet_water_temperature']: item['ejector_pressure_kPa']
            for item in ejector_results_for_one
        }

        expected_pressures = {
            35: 7.341,
            30: 5.889,
            25: 4.755,
            20: 3.879,
            15: 3.209,
            10: 2.703,
            5: 2.325,
            4: 2.263,
        }

        for temp, expected_pressure in expected_pressures.items():
            with self.subTest(temperature=temp):
                self.assertIn(temp, ejector_pressure_map, f"Результат для температуры {temp}°C не найден.")
                actual_pressure = ejector_pressure_map[temp]
                self.assertAlmostEqual(
                    actual_pressure,
                    expected_pressure,
                    places=2,
                    msg=f"Давление для t={temp}°C не совпадает"
                )

        print("\nТест: все значения давлений соответствуют эталону.")

if __name__ == '__main__':
    unittest.main()