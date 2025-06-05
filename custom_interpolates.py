import numpy as np
from scipy.interpolate import interp1d, RegularGridInterpolator


def linear_interpolation(table_data: list, target_x: float) -> float:
    """
    Выполняет линейную интерполяцию.

    Args:
        table_data: Список из двух списков [[(координаты x)], [(координаты y)]].
        target_x: Значение по X для интерполяции.

    Returns:
        Интерполированное значение по Y.
    """
    x_coords, y_coords = map(np.array, table_data)

    sort_idx = np.argsort(x_coords)
    x_sorted, y_sorted = x_coords[sort_idx], y_coords[sort_idx]

    if not np.all(np.diff(x_sorted) > 0):
        raise ValueError("Координаты X должны быть строго возрастающими после сортировки.")

    interp_func = interp1d(x_sorted, y_sorted, kind='linear', fill_value="extrapolate")
    target_y = float(interp_func(target_x))

    y_diff = np.diff(y_sorted)
    if np.all(y_diff > 0) or np.all(y_diff < 0):
        if np.all(y_diff < 0):
            x_for_reverse, y_for_reverse = x_sorted[::-1], y_sorted[::-1]
        else:
            x_for_reverse, y_for_reverse = x_sorted, y_sorted

        sort_idx_rev = np.argsort(y_for_reverse)
        y_rev_sorted = y_for_reverse[sort_idx_rev]
        x_rev_sorted = x_for_reverse[sort_idx_rev]

        if np.all(np.diff(y_rev_sorted) > 0):
            interp_reverse = interp1d(y_rev_sorted, x_rev_sorted, kind='linear', fill_value="extrapolate")
            check_x = float(interp_reverse(target_y))
            print(f"Доп. проверка: интерполированное X по Y={target_y:.3f} -> X={check_x:.3f} (исходный X={target_x})")

        x_rev, y_rev = x_coords[::-1], y_coords[::-1]
        sort_idx_rev = np.argsort(x_rev)
        x_rev_sorted, y_rev_sorted = x_rev[sort_idx_rev], y_rev[sort_idx_rev]

        if np.all(np.diff(x_rev_sorted) > 0):
            interp_rev_data = interp1d(x_rev_sorted, y_rev_sorted, kind='linear', fill_value="extrapolate")
            y_from_rev = float(interp_rev_data(target_x))
            print(
                f"Доп. проверка (развернутые данные): Y для X={target_x} -> Y={y_from_rev:.3f} (прямая интерполяция дала {target_y:.3f})")
            if not np.isclose(target_y, y_from_rev):
                print("ВНИМАНИЕ: Результаты прямой и 'развернутой' интерполяции не совпадают!")

    return target_y


def bilinear_interpolation(table_data: list, target_x: float, target_y: float) -> float:
    """
    Выполняет билинейную интерполяцию.

    Args:
        table_data: Список [[(координаты x)], [(координаты y)], [[(z)], [(z)], ...]]
        target_x: Значение по X для интерполяции.
        target_y: Значение по Y для интерполяции.

    Returns:
        Интерполированное значение по Z.
    """
    x_coords, y_coords, z_values = map(np.array, table_data)

    if np.all(np.diff(x_coords) < 0):
        x_coords = x_coords[::-1]
        z_values = z_values[::-1, :]
    elif not np.all(np.diff(x_coords) > 0):
        raise ValueError("Координаты X должны быть строго монотонными.")

    if np.all(np.diff(y_coords) < 0):
        y_coords = y_coords[::-1]
        z_values = z_values[:, ::-1]
    elif not np.all(np.diff(y_coords) > 0):
        raise ValueError("Координаты Y должны быть строго монотонными.")

    if x_coords.shape[0] != z_values.shape[0] or y_coords.shape[0] != z_values.shape[1]:
        raise ValueError(
            f"Несоответствие размерностей: X={x_coords.shape[0]}, Y={y_coords.shape[0]}, Z={z_values.shape}")

    interp_func = RegularGridInterpolator(
        (x_coords, y_coords), z_values,
        method='linear', bounds_error=False, fill_value=None
    )

    return float(interp_func([[target_x, target_y]])[0])


def linear_bilinear_interpolation(table1_data: list, table2_data: list,
                                  target_x: float, target_y: float, target_a: float) -> float:
    """
    Выполняет линейно-билинейную интерполяцию.

    Args:
        table1_data: [[A1], [(координаты x)], [(координаты y)], [[(z1)], ...]]
        table2_data: [[A2], [(координаты x)], [(координаты y)], [[(z2)], ...]]
        target_x: Значение по X.
        target_y: Значение по Y.
        target_a: Значение по A.

    Returns:
        Интерполированное значение по Z.
    """
    a1, a2 = table1_data[0][0], table2_data[0][0]

    z1_at_xy = bilinear_interpolation(table1_data[1:], target_x, target_y)
    print(f"Промежуточный Z1 (для A={a1}) при X={target_x}, Y={target_y}: {z1_at_xy:.3f}")

    z2_at_xy = bilinear_interpolation(table2_data[1:], target_x, target_y)
    print(f"Промежуточный Z2 (для A={a2}) при X={target_x}, Y={target_y}: {z2_at_xy:.3f}")

    if a1 == a2:
        if target_a != a1:
            print(f"Предупреждение: a1={a1}, a2={a2}, но target_a={target_a}. Возвращаем z1_at_xy.")
        return z1_at_xy

    a_values = np.array([a1, a2])
    z_values = np.array([z1_at_xy, z2_at_xy])

    sort_idx = np.argsort(a_values)
    a_sorted = a_values[sort_idx]
    z_sorted = z_values[sort_idx]

    interp_func = interp1d(a_sorted, z_sorted, kind='linear', fill_value="extrapolate")
    return float(interp_func(target_a))
