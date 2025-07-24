import unittest
from utils.VKU_strategy import VKUStrategy

class TestVKUStrategy(unittest.TestCase):
    """
    Набор тестов для класса VKUStrategy.
    """

    def setUp(self):
        """Настройка тестового окружения."""
        self.mass_flow_nom = 1250.0
        self.dryness_nom = 0.92
        self.strategy = VKUStrategy(
            mass_flow_steam_nom=self.mass_flow_nom,
            degree_dryness_steam_nom=self.dryness_nom
        )
        self.p_at_100_30 = 0.097280927
        self.p_at_100_20 = 0.060673115

    def test_calculation_on_grid_point(self):
        """Тест: Расчет для точки, точно совпадающей с узлом в таблице."""
        params = {
            'mass_flow_flow_path_1': 1250.0,
            'degree_dryness_flow_path_1': 0.92,
            'temperature_air': 30.0
        }
        
        result = self.strategy.calculate(params)
        
        self.assertIsInstance(result, dict)
        self.assertAlmostEqual(result['mass_flow_reduced_steam_condencer'], 100.0, places=5)
        self.assertAlmostEqual(result['pressure_flow_path_1'], self.p_at_100_30, places=7)

    def test_default_temperature(self):
        """Тест: Расчет с использованием температуры по умолчанию (20°С)."""
        params = {
            'mass_flow_flow_path_1': 1250.0,
            'degree_dryness_flow_path_1': 0.92
        }
        
        result = self.strategy.calculate(params)

        self.assertAlmostEqual(result['mass_flow_reduced_steam_condencer'], 100.0, places=5)
        self.assertAlmostEqual(result['pressure_flow_path_1'], self.p_at_100_20, places=7)

    def test_interpolation_between_points(self):
        """Тест: Расчет для точки, требующей интерполяции."""
        params = {
            'mass_flow_flow_path_1': 1187.5,
            'degree_dryness_flow_path_1': 1092.5 / 1187.5, # ~0.92
            'temperature_air': 27.5
        }
        
        result = self.strategy.calculate(params)
        
        expected_pressure_approx = 0.08341
        self.assertAlmostEqual(result['mass_flow_reduced_steam_condencer'], 95.0, places=5)
        self.assertAlmostEqual(result['pressure_flow_path_1'], expected_pressure_approx, places=3)

    def test_missing_required_param(self):
        """Тест: Проверка вызова исключения при отсутствии обязательного параметра."""
        params = {
            'degree_dryness_flow_path_1': 0.92,
            'temperature_air': 20.0
        }
        
        with self.assertRaises(KeyError):
            self.strategy.calculate(params)

if __name__ == '__main__':
    unittest.main()