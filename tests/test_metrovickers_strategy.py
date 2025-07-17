import unittest
import numpy as np

from utils.metrovickers_strategy import MetroVickersStrategy

class TestVbaLogicStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = {
            'diameter_inside_of_pipes': 0.02,
            'thickness_pipe_wall': 0.001,
            'length_cooling_tubes_of_the_main_bundle': 7.08,
            'number_cooling_tubes_of_the_main_bundle': 1754,
            'number_cooling_tubes_of_the_built-in_bundle': 0,
            'number_air_cooler_total_pipes': 418,
            'number_cooling_water_passes_of_the_main_bundle': 2,
            'thermal_conductivity_cooling_surface_tube_material': 37,
            'material_name': "сплав МНЖ5-1",

            'VAR': 2,

            'vik_table_temps': np.array([5, 15, 27, 38, 50, 70, 95, 120, 150]),
            'vik_table_speeds': np.array([0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.7]),
            'vik_table_k_values': np.array([
                [800, 1050, 1260, 1430, 1540, 1670, 1770, 1870, 1930], [1260, 1510, 1720, 1890, 2000, 2170, 2270, 2370, 2430],
                [1670, 1920, 2130, 2300, 2430, 2600, 2700, 2800, 2860], [1970, 2220, 2450, 2620, 2750, 2950, 3060, 3160, 3230],
                [2200, 2450, 2680, 2850, 2990, 3190, 3290, 3390, 3490], [2410, 2680, 2900, 3080, 3210, 3400, 3520, 3620, 3700],
                [2590, 2840, 3070, 3230, 3380, 3570, 3690, 3790, 3880], [2760, 3010, 3230, 3420, 3550, 3730, 3850, 3960, 4040],
                [2830, 3080, 3300, 3490, 3630, 3810, 3930, 4040, 4120], [2900, 3150, 3370, 3570, 3700, 3870, 4000, 4110, 4190],
                [2980, 3230, 3440, 3640, 3770, 3950, 4070, 4180, 4250], [3040, 3290, 3500, 3690, 3830, 4000, 4120, 4220, 4310],
                [3150, 3400, 3620, 3810, 3940, 4120, 4230, 4350, 4440], [3250, 3500, 3710, 3910, 4040, 4220, 4350, 4440, 4540],
                [3340, 3590, 3800, 3990, 4130, 4320, 4420, 4530, 4610], [3440, 3690, 3870, 4050, 4180, 4390, 4500, 4600, 4670],
                [3500, 3750, 3930, 4100, 4230, 4460, 4560, 4660, 4730], [3560, 3810, 3990, 4160, 4290, 4520, 4620, 4720, 4790],
                [3600, 3850, 4040, 4200, 4340, 4560, 4660, 4760, 4840], [3630, 3880, 4060, 4230, 4360, 4590, 4690, 4790, 4850]
            ]),
        }
        cls.strategy = MetroVickersStrategy(cls.params)

    def test_initialization_and_preliminary_calculations(self):
        self.assertIsNotNone(self.strategy)
        
        expected_vsr = 2484.425795437329
        self.assertAlmostEqual(self.strategy.vsr, expected_vsr, places=3)
        
    def test_calculation_against_vba_results(self):
        test_cases = [
            # ----- Таблица для β = 1.0 -----
            {'flow': 1200, 'temp': 35, 'beta': 1.0,  'expected': 0.1952242951650747},
            {'flow': 1750, 'temp': 37, 'beta': 1.0,  'expected': 0.27563651293722},
            {'flow': 2500, 'temp': 40, 'beta': 1.0,  'expected': 0.38775256003101083},
            # ----- Таблица для β = 0.75 -----
            {'flow': 1200, 'temp': 35, 'beta': 0.75, 'expected': 0.34887998869596143},
            {'flow': 1500, 'temp': 37, 'beta': 0.75, 'expected': 0.4371896897939455},
            {'flow': 2500, 'temp': 40, 'beta': 0.75, 'expected': 0.7451472306072668},
        ]

        for case in test_cases:
            with self.subTest(case=case):
                result = self.strategy.calculate_relative_underheating(
                    mass_flow=case['flow'],
                    avg_temp=case['temp'],
                    beta_coeff=case['beta']
                )
                self.assertIsNotNone(result, "Результат не должен быть None для валидных входных данных")
                self.assertAlmostEqual(result, case['expected'], places=4,
                                       msg=f"Ошибка для G={case['flow']}, t={case['temp']}, β={case['beta']}")

    def test_edge_and_out_of_bounds_conditions(self):
        result_high_speed = self.strategy.calculate_relative_underheating(5000, 35, 1.0)
        self.assertIsNone(result_high_speed, "Должен вернуть None при выходе за пределы по скорости")

        result_low_temp = self.strategy.calculate_relative_underheating(1500, 0, 1.0)
        self.assertIsNone(result_low_temp, "Должен вернуть None при выходе за пределы по температуре")
        
        result_zero_flow = self.strategy.calculate_relative_underheating(0, 35, 1.0)
        self.assertIsNone(result_zero_flow, "При нулевом расходе скорость 0, результат должен быть None")

        result_zero_beta = self.strategy.calculate_relative_underheating(1500, 35, 0)
        self.assertEqual(result_zero_beta, 0.0, "При beta=0 недогрев должен быть бесконечным (1/(exp(k*F/inf)-1))")


if __name__ == '__main__':
    unittest.main()