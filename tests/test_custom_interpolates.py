import unittest
import numpy as np
from utils.custom_interpolates import Table1D, Table2D, interpolate_trilinear, assert_table1d_reverse_consistency, \
    logger


class TestTable1D(unittest.TestCase):

    def setUp(self):
        self.x_valid = np.array([15.3, 26.8, 38.4, 49.9, 61.5, 73.0])
        self.y_valid = np.array([0.157, 0.258, 0.469, 0.607, 0.763, 0.919])
        self.table = Table1D(self.x_valid, self.y_valid)

    def test_creation_successful(self):
        self.assertIsNotNone(self.table)
        self.assertTrue(np.array_equal(self.table.x_cords,
                                       self.x_valid))  # Проверяем, что X отсортированы (в данном случае они уже были)

    def test_creation_with_unsorted_data(self):
        x_unsorted = np.array([38.4, 15.3, 73.0, 26.8, 61.5, 49.9])
        y_corresponding = np.array([0.469, 0.157, 0.919, 0.258, 0.763, 0.607])
        table_unsorted = Table1D(x_unsorted, y_corresponding)
        self.assertTrue(np.array_equal(table_unsorted.x_cords, self.x_valid))
        self.assertTrue(np.allclose(table_unsorted.y_cords, self.y_valid))
        self.assertAlmostEqual(table_unsorted(30.0), 0.316, places=3)

    def test_creation_fails_duplicate_x(self):
        x_duplicate = np.array([10.0, 20.0, 20.0, 30.0])
        y = np.array([1.0, 2.0, 2.1, 3.0])
        with self.assertRaisesRegex(ValueError,
                                    "Координаты X должны быть строго возрастающими и не содержать дубликатов"):
            Table1D(x_duplicate, y)

    def test_creation_fails_non_strictly_increasing_x(self):
        x_non_strict = np.array([10.0, 20.0, 15.0, 30.0])  # не отсортировано, но после сортировки 15<20
        y = np.array([1.0, 2.0, 1.5, 3.0])
        # После сортировки будет [10,15,20,30] - это валидно.
        # Если бы было [10,20,20,30] - это дупликат (предыдущий тест)
        # Если бы было [10,20,20.000000000000001, 30] - это валидно
        # Если бы было [10,20,19,30] после сортировки станет [10,19,20,30] - валидно
        # Ошибка возникает, если diff <=0
        x_plateau = np.array([10.0, 20.0, 20.0, 30.0])  # это дупликат
        with self.assertRaisesRegex(ValueError,
                                    "Координаты X должны быть строго возрастающими и не содержать дубликатов"):
            Table1D(x_plateau, y)

    def test_creation_fails_mismatched_sizes(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0, 2.0, 3.0])
        with self.assertRaisesRegex(ValueError, "Размеры x_cords и y_cords должны совпадать."):
            Table1D(x, y)

    def test_creation_fails_not_ndarray(self):
        with self.assertRaisesRegex(TypeError, "x_cords и y_cords должны быть экземплярами np.ndarray."):
            Table1D([1, 2], [1, 2])  # type: ignore

    def test_creation_fails_empty_arrays(self):
        with self.assertRaisesRegex(ValueError, "Массивы координат не могут быть пустыми."):
            Table1D(np.array([]), np.array([]))

    def test_interpolation_basic(self):
        self.assertAlmostEqual(self.table(30.0), 0.316, places=3)

    def test_interpolation_at_knot_points(self):
        self.assertAlmostEqual(self.table(15.3), 0.157, places=3)
        self.assertAlmostEqual(self.table(73.0), 0.919, places=3)
        self.assertAlmostEqual(self.table(38.4), 0.469, places=3)

    def test_interpolation_out_of_bounds_returns_nan(self):
        self.assertTrue(np.isnan(self.table(10.0)))  # Слева от диапазона
        self.assertTrue(np.isnan(self.table(80.0)))  # Справа от диапазона

    def test_interpolation_with_array_input(self):
        targets_x = np.array([20.0, 30.0, 73.0, 10.0])
        expected_y = np.array([0.1990196, 0.316, 0.919, np.nan])  # Расчетные или проверенные значения
        # Расчет для X=20: 0.157 + (0.258-0.157)*(20-15.3)/(26.8-15.3) = 0.157 + 0.101 * (4.7/11.5) = 0.157 + 0.101 * 0.40869 = 0.157 + 0.04127 = 0.19827
        # Мой расчет дает 0.19827, в коде было 0.1990196, это может быть связано с точностью float
        # Используем scipy для эталона
        from scipy.interpolate import interp1d as scipy_interp1d
        ref_interp = scipy_interp1d(self.x_valid, self.y_valid, kind="linear", bounds_error=False, fill_value=np.nan)
        expected_y_ref = ref_interp(targets_x)

        results = self.table(targets_x)
        self.assertTrue(np.allclose(results, expected_y_ref, equal_nan=True))

    def test_reverse_consistency_helper(self):
        """Тестирует согласованность при передаче данных в обратном порядке."""
        # Этот тест использует предложенную вспомогательную функцию
        # Он проверяет, что внутренняя сортировка Table1D работает корректно
        logger.info("Запуск assert_table1d_reverse_consistency")
        assert_table1d_reverse_consistency(self.x_valid, self.y_valid, x_test_value=30.0)
        # Проверка на граничной точке
        assert_table1d_reverse_consistency(self.x_valid, self.y_valid, x_test_value=self.x_valid[0])
        # Проверка вне диапазона (оба должны дать NaN)
        assert_table1d_reverse_consistency(self.x_valid, self.y_valid, x_test_value=self.x_valid[0] - 1)


class TestTable2D(unittest.TestCase):
    def setUp(self):
        # Данные должны быть с СТРОГО ВОЗРАСТАЮЩИМИ КООРДИНАТАМИ X и Y
        self.x_cords = np.array([25.0, 30.0, 33.0, 35.0])
        self.y_cords = np.array([20.0, 50.0, 100.0, 150.0, 200.0])
        # Z значения, соответствующие x_cords (строки) и y_cords (столбцы)
        # Исходные Z были для X = [35, 33, 30, 25] (убывающий)
        # [[для X=35], [для X=33], [для X=30], [для X=25]]
        # Разворачиваем Z по первой оси, чтобы соответствовать x_cords = [25, 30, 33, 35]
        z_original_rows_for_decreasing_x = np.array([
            [6.549, 7.211, 8.88, 10.945, 13.409],  # X=35
            [5.9, 6.499, 8.018, 9.927, 12.214],  # X=33
            [5.036, 5.552, 6.872, 8.572, 10.622],  # X=30
            [3.851, 4.257, 5.299, 6.712, 8.438]  # X=25
        ])
        self.z_values = z_original_rows_for_decreasing_x[::-1, :]
        self.table = Table2D(self.x_cords, self.y_cords, self.z_values)

        self.target_x = 27.0
        self.target_y = 112.0
        self.expected_z_basic = 6.295  # Это значение было для исходных X=[35,33,30,25]

    def test_creation_successful(self):
        self.assertIsNotNone(self.table)

    def test_creation_fails_non_strictly_increasing_x(self):
        x_invalid = np.array([25.0, 30.0, 28.0, 35.0])  # Не строго возрастающий
        with self.assertRaisesRegex(ValueError, "Координаты X .* должны быть строго возрастающими."):
            Table2D(x_invalid, self.y_cords, self.z_values)

    def test_creation_fails_non_strictly_increasing_y(self):
        y_invalid = np.array([20.0, 50.0, 40.0, 150.0, 200.0])
        with self.assertRaisesRegex(ValueError, "Координаты Y .* должны быть строго возрастающими."):
            Table2D(self.x_cords, y_invalid, self.z_values)

    def test_creation_fails_duplicate_x(self):
        x_duplicate = np.array([25.0, 30.0, 30.0, 35.0])
        z_shape_adjusted = np.random.rand(x_duplicate.shape[0], self.y_cords.shape[0])
        with self.assertRaisesRegex(ValueError, "Координаты X .* должны быть строго возрастающими."):
            Table2D(x_duplicate, self.y_cords, z_shape_adjusted)

    def test_creation_fails_mismatched_z_shape(self):
        z_wrong_shape = np.random.rand(self.x_cords.size, self.y_cords.size + 1)
        with self.assertRaisesRegex(ValueError, "Форма z_values .* не соответствует ожидаемой"):
            Table2D(self.x_cords, self.y_cords, z_wrong_shape)

        z_wrong_shape_2 = np.random.rand(self.x_cords.size + 1, self.y_cords.size)
        with self.assertRaisesRegex(ValueError, "Форма z_values .* не соответствует ожидаемой"):
            Table2D(self.x_cords, self.y_cords, z_wrong_shape_2)

    def test_interpolation_basic(self):
        result = self.table(self.target_x, self.target_y)
        self.assertAlmostEqual(float(result), self.expected_z_basic, places=3)

    def test_interpolation_at_grid_points(self):
        # (25, 20) -> z_values[0,0]
        self.assertAlmostEqual(float(self.table(25.0, 20.0)), self.z_values[0, 0], places=3)
        # (35, 200) -> z_values[-1,-1]
        self.assertAlmostEqual(float(self.table(35.0, 200.0)), self.z_values[-1, -1], places=3)
        # (30, 100) -> z_values[1,2]
        self.assertAlmostEqual(float(self.table(30.0, 100.0)), self.z_values[1, 2], places=3)

    def test_interpolation_out_of_bounds_returns_nan(self):
        self.assertTrue(np.isnan(self.table(20.0, 50.0)))  # X слева
        self.assertTrue(np.isnan(self.table(40.0, 50.0)))  # X справа
        self.assertTrue(np.isnan(self.table(30.0, 10.0)))  # Y снизу
        self.assertTrue(np.isnan(self.table(30.0, 250.0)))  # Y сверху
        self.assertTrue(np.isnan(self.table(10.0, 10.0)))  # Оба вне

    def test_interpolation_with_array_inputs(self):
        xs = np.array([27.0, 30.0, 20.0]) # 20.0 is out of bounds
        ys = np.array([112.0, 100.0, 50.0])#

        expected_zs_manual = np.array([
            self.expected_z_basic, # For (27, 112)
            self.z_values[1,2],    # For (30, 100) - a grid point
            np.nan                 # For (20, 50) - out of bounds
        ])

        results = self.table(xs, ys)
        self.assertTrue(results.shape == xs.shape)
        self.assertTrue(np.allclose(results, expected_zs_manual, equal_nan=True, atol=1e-3))


class TestInterpolateTrilinear(unittest.TestCase):
    def setUp(self):
        self.x_cords = np.array([25.0, 30.0, 33.0, 35.0])
        self.y_cords = np.array([20.0, 50.0, 100.0, 150.0, 200.0])

        z_a1_original = np.array([  # Corresponds to X=[35,33,30,25]
            [6.549, 7.211, 8.88, 10.945, 13.409], [5.9, 6.499, 8.018, 9.927, 12.214],
            [5.036, 5.552, 6.872, 8.572, 10.622], [3.851, 4.257, 5.299, 6.712, 8.438]
        ])
        z_a2_original = np.array([  # Corresponds to X=[35,33,30,25]
            [6.635, 7.384, 9.285, 11.678, 14.582], [5.979, 6.655, 8.384, 10.591, 13.28],
            [5.104, 5.687, 7.184, 9.144, 11.546], [3.906, 4.362, 5.539, 7.158, 9.169]
        ])

        self.z_a1 = z_a1_original[::-1, :]  # For sorted self.x_cords
        self.z_a2 = z_a2_original[::-1, :]  # For sorted self.x_cords

        self.table_a1 = Table2D(self.x_cords, self.y_cords, self.z_a1)  # A = 9000
        self.table_a2 = Table2D(self.x_cords, self.y_cords, self.z_a2)  # A = 8000

        self.a_val1 = 9000.0
        self.a_val2 = 8000.0

        self.target_x = 27.0
        self.target_y = 112.0
        # Z1 (A=9000) for (27, 112) is 6.295
        # Z2 (A=8000) for (27, 112) is 6.618
        # For target_a = 8800: 6.618 + (6.295 - 6.618) * ((8800-8000)/(9000-8000)) = 6.3596
        self.expected_z_trilinear = 6.3596

    def test_basic_trilinear_interpolation(self):
        # Note: interpolate_trilinear expects a_low < a_high in its argument name, but np.interp handles order
        # For clarity, we pass them in sorted order for 'a_low' and 'a_high' params.
        result = interpolate_trilinear(self.table_a2, self.a_val2,  # table for lower A, value of lower A
                                       self.table_a1, self.a_val1,  # table for higher A, value of higher A
                                       self.target_x, self.target_y, target_a=8800.0)
        self.assertAlmostEqual(result, self.expected_z_trilinear, places=3)

    def test_trilinear_at_a_boundaries(self):
        # Target A = a_val1 (9000)
        expected_z_at_a1 = float(self.table_a1(self.target_x, self.target_y))
        result1 = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                        self.target_x, self.target_y, target_a=self.a_val1)
        self.assertAlmostEqual(result1, expected_z_at_a1, places=3)

        # Target A = a_val2 (8000)
        expected_z_at_a2 = float(self.table_a2(self.target_x, self.target_y))
        result2 = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                        self.target_x, self.target_y, target_a=self.a_val2)
        self.assertAlmostEqual(result2, expected_z_at_a2, places=3)

    def test_trilinear_extrapolation_a(self):
        # Extrapolate A below a_val2 (8000) -> e.g. 7500
        expected_low_a = float(self.table_a2(self.target_x, self.target_y))
        result_low_a = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                             self.target_x, self.target_y, target_a=7500.0)
        self.assertAlmostEqual(result_low_a, expected_low_a, places=3)

        # Extrapolate A above a_val1 (9000) -> e.g. 9500
        expected_high_a = float(self.table_a1(self.target_x, self.target_y))
        result_high_a = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                              self.target_x, self.target_y, target_a=9500.0)
        self.assertAlmostEqual(result_high_a, expected_high_a, places=3)

    def test_trilinear_a_low_equals_a_high(self):
        val_a = 8500.0
        z_expected = float(self.table_a1(self.target_x, self.target_y))

        result_same_a_target_matches = interpolate_trilinear(
            self.table_a1, val_a, self.table_a1, val_a,
            self.target_x, self.target_y, target_a=val_a
        )
        self.assertAlmostEqual(result_same_a_target_matches, z_expected, places=3)

    def test_trilinear_intermediate_nan(self):
        x_cords_nan = np.array([1.0, 2.0])
        y_cords_nan = np.array([1.0, 2.0])
        z_values_nan = np.array([[1.0, 2.0], [3.0, 4.0]])
        table_nan = Table2D(x_cords_nan, y_cords_nan, z_values_nan)

        result = interpolate_trilinear(table_nan, self.a_val2, self.table_a1, self.a_val1,
                                       self.target_x, self.target_y, target_a=8800.0)
        self.assertTrue(np.isnan(result))

        result2 = interpolate_trilinear(self.table_a2, self.a_val2, table_nan, self.a_val1,
                                        self.target_x, self.target_y, target_a=8800.0)
        self.assertTrue(np.isnan(result2))


if __name__ == '__main__':
    unittest.main()
