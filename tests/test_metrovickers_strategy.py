import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metrovickers_strategy import MetroVickersStrategy

class TestMetroVickersStrategy(unittest.TestCase):
    """
    Тесты для класса MetroVickersStrategy с полными именами переменных.
    """

    def setUp(self):
        """
        Настройка перед каждым тестом.
        """
        self.strategy = MetroVickersStrategy()
        self.test_params = {
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

    def test_calculation_runs_without_errors(self):
        """
        Проверяет, что расчет выполняется без падений.
        """
        results = None
        try:
            results = self.strategy.calculate(self.test_params)
        except Exception as e:
            self.fail(f"Метод calculate() вызвал исключение: {e}")
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, dict)

    def test_key_output_values(self):
        """
        Проверяет наличие и типы ключевых выходных параметров.
        """
        results = self.strategy.calculate(self.test_params)
        
        expected_keys = [
            'diameter_outside_of_pipes', 'area_tube_bundle_surface_total',
            'coefficient_Kf', 'coefficient_R1', 'speed_cooling_water',
            'coefficient_K_temp', 'coefficient_K', 'coefficient_R',
            'heat_of_vaporization', 'temperature_cooling_water_2',
            'temperature_cooling_water_average_heating', 'coefficient_Kzag',
            'temperature_relative_underheating', 'temperature_saturation_steam',
            'pressure_flow_path_1'
        ]
        for key in expected_keys:
            self.assertIn(key, results, f"Ключ '{key}' отсутствует в результатах")

    def test_logic_checks(self):
        """
        Выполняет логические проверки результатов.
        """
        results = self.strategy.calculate(self.test_params)

        self.assertGreater(results['diameter_outside_of_pipes'], self.test_params['diameter_inside_of_pipes'])
        self.assertAlmostEqual(results['diameter_outside_of_pipes'], 24.0)
        
        self.assertGreater(results['temperature_cooling_water_2'], self.test_params['temperature_cooling_water_1'])
        
        self.assertGreater(results['temperature_saturation_steam'], 0)
        self.assertGreater(results['pressure_flow_path_1'], 0)
        
        self.assertLess(results['coefficient_Kzag'], results['coefficient_K'])

    def test_optional_n_vo_calculation(self):
        """
        Проверяет, что Nво правильно рассчитывается, если не предоставлен.
        """
        results_auto = self.strategy.calculate(self.test_params)
        
        params_manual = self.test_params.copy()
        N_op = params_manual['number_cooling_tubes_of_the_main_bundle']
        N_vp = params_manual['number_cooling_tubes_of_the_built_in_bundle']
        params_manual['number_air_cooler_total_pipes'] = (N_op + N_vp) * 0.15
        
        results_manual = self.strategy.calculate(params_manual)
        
        self.assertAlmostEqual(
            results_auto['pressure_flow_path_1'], 
            results_manual['pressure_flow_path_1']
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)