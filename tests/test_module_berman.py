import unittest
import copy
from utils.module_berman import calculate_thermal_characteristics 

class TestKondensatorCalculations(unittest.TestCase):

    def setUp(self):
        self.test_params = {
            'A': {1: 1.0, 2: 1.0},
            'Z': {1: 2, 2: 2},
            'FN': {1: 10000, 2: 3000},
            'DI': 520.0,
            'DK': 540.0,
            'DLCT': 37.0,
            'BAP': 3,
            'DD': 22.0 / 1000.0,
            'DCT': 1.0 / 1000.0,
            'W': [
                [14215.0],
                [3285.0]
            ],
            'T1': [
                [27.5, 32.0],
                [27.5, 32.0]
            ],
            'D': [30.0, 80.0, 130.0, 180.0, 230.0],
            'R': [0.1, 104.4], 
            'RBETA': [0.0, 1.0], 
            'GV': 20.0
        }

    def test_calculation_with_report_data(self):
        """
        Тестирует основной сценарий расчета и сверяет с данными из эталонного отчета.
        """
        results = calculate_thermal_characteristics(self.test_params)
        main_results = results['main_results']

        self.assertGreater(len(main_results), 0, "Расчет не вернул результатов.")
        self.assertEqual(len(main_results), 20, "Неверное количество строк в результате")

        res_r1_t1_d1 = main_results[0]
        self.assertAlmostEqual(res_r1_t1_d1['TK'], 53.365, places=3)
        self.assertAlmostEqual(res_r1_t1_d1['PS'], 0.14849, places=5)
        self.assertAlmostEqual(res_r1_t1_d1['T4_1'], 24.991, places=3)

        res_r1_t1_d5 = main_results[4]
        self.assertAlmostEqual(res_r1_t1_d5['TK'], 71.192, places=3)
        self.assertAlmostEqual(res_r1_t1_d5['PS'], 0.33471, places=5)

        res_r1_t2_d1 = main_results[5]
        self.assertAlmostEqual(res_r1_t2_d1['TK'], 55.147, places=3)
        self.assertAlmostEqual(res_r1_t2_d1['PS'], 0.16181, places=5)

        res_r2_t1_d1 = main_results[10]
        self.assertAlmostEqual(res_r2_t1_d1['TK'], 55.033, places=3)
        self.assertAlmostEqual(res_r2_t1_d1['PS'], 0.16092, places=5)

        res_r2_t2_d5 = main_results[19]
        self.assertAlmostEqual(res_r2_t2_d5['TK'], 86.396, places=3)
        self.assertAlmostEqual(res_r2_t2_d5['PS'], 0.62250, places=5)

    def test_ejector_calculation_with_report_data(self):
        """
        Тестирует расчет характеристик с учетом эжектора по данным отчета.
        """
        results = calculate_thermal_characteristics(self.test_params)
        ejector_results = results['ejector_results']

        self.assertIsNotNone(ejector_results)
        self.assertEqual(len(ejector_results['temps']), 2)

        self.assertAlmostEqual(ejector_results['pk_values_1'][0], 6.533, places=3) # для t=32.0
        self.assertAlmostEqual(ejector_results['pk_values_1'][1], 5.391, places=3) # для t=27.5

        self.assertAlmostEqual(ejector_results['pk_values_2'][0], 6.233, places=3) # для t=32.0
        self.assertAlmostEqual(ejector_results['pk_values_2'][1], 5.091, places=3) # для t=27.5
        
    def test_one_pass_condenser_logic(self):
        """
        Тестирует расчет для одноходового конденсатора (BAP=1).
        Этот тест остается без изменений, так как он проверяет логику, а не значения.
        """
        one_pass_params = copy.deepcopy(self.test_params)
        one_pass_params['BAP'] = 1
        
        results = calculate_thermal_characteristics(one_pass_params)
        main_results = results['main_results']
        
        self.assertGreater(len(main_results), 0)

        for row in main_results:
            self.assertEqual(row['FKD2'], 0)
            self.assertEqual(row['T3_2'], 0)
            self.assertEqual(row['T4_2'], 0)

    def test_no_ejector_data(self):
        """
        Тестирует поведение, когда данные для эжектора отсутствуют (GV=0).
        Этот тест также остается без изменений.
        """
        no_ejector_params = copy.deepcopy(self.test_params)
        no_ejector_params['GV'] = 0
        
        results = calculate_thermal_characteristics(no_ejector_params)
        ejector_results = results['ejector_results']
        
        self.assertEqual(len(ejector_results['temps']), 0)
        self.assertEqual(len(ejector_results['pk_values_1']), 0)
        self.assertEqual(len(ejector_results['pk_values_2']), 0)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)