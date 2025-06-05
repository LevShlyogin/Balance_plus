import unittest
from custom_interpolates import linear_interpolation, bilinear_interpolation, linear_bilinear_interpolation


class TestLinearInterpolation(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных"""
        self.tab = [[15.3, 26.8, 38.4, 49.9, 61.5, 73],
                    [0.157, 0.258, 0.469, 0.607, 0.763, 0.919]]
        self.x = 30
        self.expected_y = 0.316

    def test_linear_interpolation_basic(self):
        """Тест базовой линейной интерполяции"""
        result = linear_interpolation(self.tab, self.x)
        self.assertAlmostEqual(result, self.expected_y, places=3)

    def test_linear_interpolation_reversed_data(self):
        """Тест с развернутыми данными"""
        # Разворачиваем X и Y
        tab_reversed = [self.tab[0][::-1], self.tab[1][::-1]]
        result = linear_interpolation(tab_reversed, self.x)
        self.assertAlmostEqual(result, self.expected_y, places=3)

    def test_linear_interpolation_edge_cases(self):
        """Тест граничных случаев"""
        # Интерполяция в начальной точке
        result = linear_interpolation(self.tab, 15.3)
        self.assertAlmostEqual(result, 0.157, places=3)

        # Интерполяция в конечной точке
        result = linear_interpolation(self.tab, 73)
        self.assertAlmostEqual(result, 0.919, places=3)

    def test_linear_interpolation_extrapolation(self):
        """Тест экстраполяции"""
        # Экстраполяция за пределы диапазона
        result_low = linear_interpolation(self.tab, 10)
        result_high = linear_interpolation(self.tab, 80)

        # Проверяем, что функция возвращает результат (не падает)
        self.assertIsInstance(result_low, float)
        self.assertIsInstance(result_high, float)

    def test_linear_interpolation_unsorted_data(self):
        """Тест с несортированными данными"""
        # Перемешиваем данные
        indices = [2, 0, 4, 1, 5, 3]
        tab_unsorted = [[self.tab[0][i] for i in indices],
                        [self.tab[1][i] for i in indices]]

        result = linear_interpolation(tab_unsorted, self.x)
        self.assertAlmostEqual(result, self.expected_y, places=3)


class TestBilinearInterpolation(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных"""
        self.tab = [[35, 33, 30, 25],
                    [20, 50, 100, 150, 200],
                    [[6.549, 7.211, 8.88, 10.945, 13.409],
                     [5.9, 6.499, 8.018, 9.927, 12.214],
                     [5.036, 5.552, 6.872, 8.572, 10.622],
                     [3.851, 4.257, 5.299, 6.712, 8.438]]]
        self.x = 27
        self.y = 112
        self.expected_z = 7.758

    def test_bilinear_interpolation_basic(self):
        """Тест базовой билинейной интерполяции"""
        result = bilinear_interpolation(self.tab, self.x, self.y)
        self.assertAlmostEqual(result, self.expected_z, places=3)

    def test_bilinear_interpolation_grid_points(self):
        """Тест интерполяции в узлах сетки"""
        # Проверяем точку (35, 20)
        result = bilinear_interpolation(self.tab, 35, 20)
        self.assertAlmostEqual(result, 6.549, places=3)

        # Проверяем точку (25, 200)
        result = bilinear_interpolation(self.tab, 25, 200)
        self.assertAlmostEqual(result, 8.438, places=3)

    def test_bilinear_interpolation_edge_interpolation(self):
        """Тест интерполяции на границах"""
        # Интерполяция по X при фиксированном Y=50
        result = bilinear_interpolation(self.tab, 32, 50)
        # Проверяем, что результат между значениями в точках (33,50) и (30,50)
        self.assertGreater(result, min(6.499, 5.552))
        self.assertLess(result, max(6.499, 5.552))

    def test_bilinear_interpolation_reversed_coordinates(self):
        """Тест с убывающими координатами"""
        # X уже убывает в исходных данных, проверим это
        result = bilinear_interpolation(self.tab, self.x, self.y)
        self.assertAlmostEqual(result, self.expected_z, places=3)

        # Создадим таблицу с убывающими Y
        tab_reversed_y = [
            self.tab[0],
            self.tab[1][::-1],
            [row[::-1] for row in self.tab[2]]
        ]
        result = bilinear_interpolation(tab_reversed_y, self.x, self.y)
        self.assertAlmostEqual(result, self.expected_z, places=3)


class TestLinearBilinearInterpolation(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных"""
        self.tab_1 = [[9000],
                      [35, 33, 30, 25],
                      [20, 50, 100, 150, 200],
                      [[6.549, 7.211, 8.88, 10.945, 13.409],
                       [5.9, 6.499, 8.018, 9.927, 12.214],
                       [5.036, 5.552, 6.872, 8.572, 10.622],
                       [3.851, 4.257, 5.299, 6.712, 8.438]]]

        self.tab_2 = [[8000],
                      [35, 33, 30, 25],
                      [20, 50, 100, 150, 200],
                      [[6.635, 7.384, 9.285, 11.678, 14.582],
                       [5.979, 6.655, 8.384, 10.591, 13.28],
                       [5.104, 5.687, 7.184, 9.144, 11.546],
                       [3.906, 4.362, 5.539, 7.158, 9.169]]]

        self.x = 27
        self.y = 112
        self.a = 8800

        # Вычисляем ожидаемый результат
        # Z1 при A=9000: 7.758 (из предыдущего теста)
        # Z2 при A=8000: нужно вычислить
        z2_at_xy = bilinear_interpolation(self.tab_2[1:], self.x, self.y)
        # Линейная интерполяция между z1=7.758 и z2
        # При A=8800: Z = z2 + (z1-z2) * (8800-8000)/(9000-8000)
        self.expected_z = z2_at_xy + (7.758 - z2_at_xy) * 0.8

    def test_linear_bilinear_interpolation_basic(self):
        """Тест базовой линейно-билинейной интерполяции"""
        result = linear_bilinear_interpolation(self.tab_1, self.tab_2,
                                               self.x, self.y, self.a)
        # Проверяем, что результат находится между значениями для A=8000 и A=9000
        z1 = bilinear_interpolation(self.tab_1[1:], self.x, self.y)
        z2 = bilinear_interpolation(self.tab_2[1:], self.x, self.y)
        self.assertGreater(result, min(z1, z2))
        self.assertLess(result, max(z1, z2))

        # Более точная проверка
        self.assertAlmostEqual(result, self.expected_z, places=3)

    def test_linear_bilinear_interpolation_at_boundaries(self):
        """Тест интерполяции на границах по A"""
        # При A=9000 должны получить результат из первой таблицы
        result = linear_bilinear_interpolation(self.tab_1, self.tab_2,
                                               self.x, self.y, 9000)
        z1 = bilinear_interpolation(self.tab_1[1:], self.x, self.y)
        self.assertAlmostEqual(result, z1, places=3)

        # При A=8000 должны получить результат из второй таблицы
        result = linear_bilinear_interpolation(self.tab_1, self.tab_2,
                                               self.x, self.y, 8000)
        z2 = bilinear_interpolation(self.tab_2[1:], self.x, self.y)
        self.assertAlmostEqual(result, z2, places=3)

    def test_linear_bilinear_interpolation_extrapolation(self):
        """Тест экстраполяции по A"""
        # Экстраполяция за пределы диапазона A
        result_low = linear_bilinear_interpolation(self.tab_1, self.tab_2,
                                                   self.x, self.y, 7500)
        result_high = linear_bilinear_interpolation(self.tab_1, self.tab_2,
                                                    self.x, self.y, 9500)

        # Проверяем, что функция возвращает результаты
        self.assertIsInstance(result_low, float)
        self.assertIsInstance(result_high, float)

    def test_linear_bilinear_interpolation_same_a_values(self):
        """Тест случая с одинаковыми значениями A"""
        # Создаем две таблицы с одинаковым A
        tab_same_a = [[8000],
                      [35, 33, 30, 25],
                      [20, 50, 100, 150, 200],
                      self.tab_1[3]]

        result = linear_bilinear_interpolation(tab_same_a, self.tab_2,
                                               self.x, self.y, 8000)
        # Должен вернуть значение из первой таблицы
        z1 = bilinear_interpolation(tab_same_a[1:], self.x, self.y)
        self.assertAlmostEqual(result, z1, places=3)


def calculate_expected_z_for_linear_bilinear():
    """Вспомогательная функция для вычисления ожидаемого Z"""
    # Данные из задачи
    tab_1 = [[9000],
             [35, 33, 30, 25],
             [20, 50, 100, 150, 200],
             [[6.549, 7.211, 8.88, 10.945, 13.409],
              [5.9, 6.499, 8.018, 9.927, 12.214],
              [5.036, 5.552, 6.872, 8.572, 10.622],
              [3.851, 4.257, 5.299, 6.712, 8.438]]]

    tab_2 = [[8000],
             [35, 33, 30, 25],
             [20, 50, 100, 150, 200],
             [[6.635, 7.384, 9.285, 11.678, 14.582],
              [5.979, 6.655, 8.384, 10.591, 13.28],
              [5.104, 5.687, 7.184, 9.144, 11.546],
              [3.906, 4.362, 5.539, 7.158, 9.169]]]

    x, y, a = 27, 112, 8800

    # Вычисляем Z для обеих таблиц
    z1 = bilinear_interpolation(tab_1[1:], x, y)  # ≈ 7.758
    z2 = bilinear_interpolation(tab_2[1:], x, y)  # нужно вычислить

    print(f"Z1 (A=9000): {z1:.3f}")
    print(f"Z2 (A=8000): {z2:.3f}")

    # Линейная интерполяция по A
    # Z = Z2 + (Z1 - Z2) * (A - A2) / (A1 - A2)
    z_result = z2 + (z1 - z2) * (a - 8000) / (9000 - 8000)
    print(f"Z при A={a}: {z_result:.3f}")

    return z_result


if __name__ == '__main__':
    # Вычисляем ожидаемое значение Z для третьего примера
    print("Вычисление ожидаемого Z для линейно-билинейной интерполяции:")
    expected_z = calculate_expected_z_for_linear_bilinear()
    print(f"\nОжидаемое значение Z = {expected_z:.3f}")

    # Запускаем тесты
    unittest.main(argv=[''], exit=False)
