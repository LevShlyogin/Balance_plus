from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from scipy.interpolate import interp1d, RegularGridInterpolator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Table1D:
    """
    Представляет 1D таблицу для линейной интерполяции.
    Координаты x сортируются при создании, и значения y соответственно.
    Предполагается, что координаты x после сортировки будут строго возрастающими.
    """
    x_cords: np.ndarray
    y_cords: np.ndarray
    _interp: interp1d = field(init=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.x_cords, np.ndarray) or not isinstance(self.y_cords, np.ndarray):
            raise TypeError("x_cords и y_cords должны быть экземплярами np.ndarray.")
        if self.x_cords.ndim != 1 or self.y_cords.ndim != 1:
            raise ValueError("x_cords и y_cords должны быть 1-мерными массивами.")
        if self.x_cords.size != self.y_cords.size:
            raise ValueError("Размеры x_cords и y_cords должны совпадать.")
        if self.x_cords.size == 0:
            raise ValueError("Массивы координат не могут быть пустыми.")

        sort_indices = np.argsort(self.x_cords)
        x_sorted = self.x_cords[sort_indices]
        y_sorted = self.y_cords[sort_indices]

        # Проверка на строгое возрастание и отсутствие дубликатов X
        if np.any(np.diff(x_sorted) <= 0):
            raise ValueError(
                "Координаты X должны быть строго возрастающими и не содержать дубликатов после сортировки.")

        object.__setattr__(self, 'x_cords', x_sorted)
        object.__setattr__(self, 'y_cords', y_sorted)

        # Создаем интерполятор один раз
        interp_func = interp1d(x_sorted, y_sorted, kind="linear",
                               bounds_error=False, fill_value=np.nan)
        object.__setattr__(self, '_interp', interp_func)

    def __call__(self, target_x: float | np.ndarray) -> float | np.ndarray:
        """
        Выполняет интерполяцию для target_x.
        Может принимать скаляр или массив NumPy.
        """
        return self._interp(target_x)


@dataclass(frozen=True)
class Table2D:
    """
    Представляет 2D таблицу для билинейной интерполяции.
    Координаты x и y должны быть 1D массивами, строго возрастающими.
    z_values должен быть 2D массивом с формой (len(x_cords), len(y_cords)).
    """
    x_cords: np.ndarray
    y_cords: np.ndarray
    z_values: np.ndarray
    _rgi: RegularGridInterpolator = field(init=False, repr=False)

    def __post_init__(self):
        if not all(isinstance(arr, np.ndarray) for arr in [self.x_cords, self.y_cords, self.z_values]):
            raise TypeError("x_cords, y_cords, и z_values должны быть экземплярами np.ndarray.")
        if self.x_cords.ndim != 1 or self.y_cords.ndim != 1:
            raise ValueError("x_cords и y_cords должны быть 1-мерными массивами.")
        if self.z_values.ndim != 2:
            raise ValueError("z_values должен быть 2-мерным массивом.")
        if self.x_cords.size == 0 or self.y_cords.size == 0:
            raise ValueError("Массивы координат не могут быть пустыми.")

        if np.any(np.diff(self.x_cords) <= 0):
            raise ValueError("Координаты X (x_cords) должны быть строго возрастающими.")
        if np.any(np.diff(self.y_cords) <= 0):
            raise ValueError("Координаты Y (y_cords) должны быть строго возрастающими.")

        # Проверка соответствия размерностей z_values с x_cords и y_cords
        if self.z_values.shape != (self.x_cords.size, self.y_cords.size):
            raise ValueError(f"Форма z_values {self.z_values.shape} не соответствует ожидаемой "
                             f"({self.x_cords.size}, {self.y_cords.size}) на основе x_cords и y_cords.")

        # Создаем интерполятор один раз
        rgi_func = RegularGridInterpolator((self.x_cords, self.y_cords), self.z_values,
                                           method="linear",
                                           bounds_error=False, fill_value=np.nan)
        object.__setattr__(self, '_rgi', rgi_func)

    def __call__(self, target_x: float | np.ndarray,
                 target_y: float | np.ndarray) -> float | np.ndarray:
        """
        Выполняет билинейную интерполяцию для пар (target_x, target_y).
        target_x и target_y могут быть скалярами или массивами NumPy.
        Если массивы, они должны иметь одинаковую форму.
        """
        # Подготовка точек для RegularGridInterpolator
        points_x = np.ravel(target_x)
        points_y = np.ravel(target_y)
        if points_x.shape != points_y.shape:
            raise ValueError("Формы target_x и target_y должны совпадать, если они являются массивами.")

        points_to_interpolate = np.column_stack((points_x, points_y))
        interpolated_values = self._rgi(points_to_interpolate)

        return interpolated_values.reshape(np.shape(target_x))


def interpolate_trilinear(
        table_low_a: Table2D, a_low: float,
        table_high_a: Table2D, a_high: float,
        target_x: float, target_y: float, target_a: float) -> float:
    """
    Выполняет линейно-билинейную (трилинейную) интерполяцию.
    Сначала выполняется билинейная интерполяция для target_x, target_y
    в table_low_a и table_high_a.
    Затем выполняется линейная интерполяция по target_a между полученными значениями.

    Args:
        table_low_a: Объект Table2D для нижнего значения параметра A.
        a_low: Значение параметра A, соответствующее table_low_a.
        table_high_a: Объект Table2D для верхнего значения параметра A.
        a_high: Значение параметра A, соответствующее table_high_a.
        target_x: Целевое значение X.
        target_y: Целевое значение Y.
        target_a: Целевое значение A.

    Returns:
        Интерполированное значение Z.
    """
    if a_low == a_high:
        if target_a == a_low:
            logger.info(f"a_low ({a_low}) и a_high ({a_high}) равны, target_a ({target_a}) совпадает. "
                        f"Используется table_low_a.")
            return float(table_low_a(target_x, target_y))
        else:
            logger.warning(f"a_low ({a_low}) и a_high ({a_high}) равны, но target_a ({target_a}) отличается. "
                           f"Результат будет основан на значениях для a_low/a_high.")

    # Шаг 1: Билинейная интерполяция для table_low_a и table_high_a
    z_at_a_low = table_low_a(target_x, target_y)
    z_at_a_high = table_high_a(target_x, target_y)

    # Шаг 2: Линейная интерполяция
    if isinstance(z_at_a_low, np.ndarray) and z_at_a_low.size == 1:
        z_at_a_low = float(z_at_a_low.item())
    if isinstance(z_at_a_high, np.ndarray) and z_at_a_high.size == 1:
        z_at_a_high = float(z_at_a_high.item())

    # Проверка на NaN перед интерполяцией по A
    if np.isnan(z_at_a_low) or np.isnan(z_at_a_high):
        logger.warning(f"Один из промежуточных Z является NaN (Z_low={z_at_a_low}, Z_high={z_at_a_high}). "
                       f"Результат интерполяции по A также будет NaN.")
        return np.nan

    final_z = np.interp(target_a, [a_low, a_high], [z_at_a_low, z_at_a_high])

    return float(final_z)


def assert_table1d_reverse_consistency(original_x: np.ndarray, original_y: np.ndarray, x_test_value: float, atol=1e-12):
    """
    Проверяет, что Table1D дает тот же результат для x_test_value,
    даже если исходные данные x и y были переданы в обратном порядке.
    Это возможно благодаря внутренней сортировке в Table1D.
    """
    table_normal_order = Table1D(original_x, original_y)
    y_normal = table_normal_order(x_test_value)

    table_reversed_input_order = Table1D(original_x[::-1], original_y[::-1])
    y_reversed_input = table_reversed_input_order(x_test_value)

    if np.isnan(y_normal) and np.isnan(y_reversed_input):
        return
    elif np.isnan(y_normal) or np.isnan(y_reversed_input):
        raise AssertionError(f"Несоответствие NaN при проверке обратного порядка: {y_normal} vs {y_reversed_input}")

    assert np.isclose(y_normal, y_reversed_input, atol=atol), \
        f"Несоответствие при проверке обратного порядка: {y_normal} vs {y_reversed_input} для X={x_test_value}"
    logger.debug(f"Проверка обратной согласованности для X={x_test_value} пройдена: Y={y_normal}")
