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
    x_coords = np.array(table_data[0])
    y_coords = np.array(table_data[1])

    sort_indices = np.argsort(x_coords)
    x_coords_sorted = x_coords[sort_indices]
    y_coords_sorted = y_coords[sort_indices]

    if not np.all(np.diff(x_coords_sorted) > 0):
        raise ValueError("Координаты X должны быть строго возрастающими после сортировки.")

    interp_func = interp1d(x_coords_sorted, y_coords_sorted, kind='linear', fill_value="extrapolate")
    target_y = float(interp_func(target_x))

    if np.all(np.diff(y_coords_sorted) > 0) or np.all(np.diff(y_coords_sorted) < 0):
        if np.all(np.diff(y_coords_sorted) < 0):
            y_coords_for_reverse = y_coords_sorted[::-1]
            x_coords_for_reverse = x_coords_sorted[::-1]
        else:
            y_coords_for_reverse = y_coords_sorted
            x_coords_for_reverse = x_coords_sorted

        sort_indices_rev = np.argsort(y_coords_for_reverse)
        y_coords_for_reverse_sorted = y_coords_for_reverse[sort_indices_rev]
        x_coords_for_reverse_sorted = x_coords_for_reverse[sort_indices_rev]

        if np.all(np.diff(y_coords_for_reverse_sorted) > 0):
            interp_func_reverse = interp1d(y_coords_for_reverse_sorted, x_coords_for_reverse_sorted, kind='linear',
                                           fill_value="extrapolate")
            check_x = float(interp_func_reverse(target_y))
            print(f"Доп. проверка: интерполированное X по Y={target_y:.3f} -> X={check_x:.3f} (исходный X={target_x})")
        else:
            print("Доп. проверка: Y-координаты не монотонны, обратная интерполяция для проверки пропущена.")

        x_reversed_original_order = x_coords[::-1]
        y_reversed_original_order = y_coords[::-1]

        sort_indices_rev_order = np.argsort(x_reversed_original_order)
        x_rev_sorted = x_reversed_original_order[sort_indices_rev_order]
        y_rev_sorted = y_reversed_original_order[sort_indices_rev_order]

        if np.all(np.diff(x_rev_sorted) > 0):
            interp_func_rev_data = interp1d(x_rev_sorted, y_rev_sorted, kind='linear', fill_value="extrapolate")
            y_from_rev_data = float(interp_func_rev_data(target_x))
            print(
                f"Доп. проверка (развернутые данные): Y для X={target_x} -> Y={y_from_rev_data:.3f} (прямая интерполяция дала {target_y:.3f})")
            if not np.isclose(target_y, y_from_rev_data):
                print("ВНИМАНИЕ: Результаты прямой и 'развернутой' интерполяции не совпадают!")
        else:
            print(
                "Доп. проверка (развернутые данные): X-координаты после разворота и сортировки не монотонны, проверка пропущена.")

    return target_y


def bilinear_interpolation(table_data: list, target_x: float, target_y: float) -> float:
    """
    Выполняет билинейную интерполяцию.

    Args:
        table_data: Список [[(координаты x)], [(координаты y)], [[(z)], [(z)], ...]]
                    где z - это сетка значений.
        target_x: Значение по X для интерполяции.
        target_y: Значение по Y для интерполяции.

    Returns:
        Интерполированное значение по Z.
    """
    x_coords = np.array(table_data[0])
    y_coords = np.array(table_data[1])
    z_values = np.array(table_data[2])

    if np.all(np.diff(x_coords) < 0):
        x_coords = x_coords[::-1]
        z_values = z_values[::-1, :]
    elif not np.all(np.diff(x_coords) > 0):
        raise ValueError("Координаты X должны быть строго монотонными (возрастающими или убывающими).")

    if np.all(np.diff(y_coords) < 0):
        y_coords = y_coords[::-1]
        z_values = z_values[:, ::-1]
    elif not np.all(np.diff(y_coords) > 0):
        raise ValueError("Координаты Y должны быть строго монотонными (возрастающими или убывающими).")

    if x_coords.shape[0] != z_values.shape[0]:
        raise ValueError(
            f"Размерность X ({x_coords.shape[0]}) не совпадает с первой размерностью Z ({z_values.shape[0]}). Возможно, Z нужно транспонировать?")
    if y_coords.shape[0] != z_values.shape[1]:
        raise ValueError(
            f"Размерность Y ({y_coords.shape[0]}) не совпадает со второй размерностью Z ({z_values.shape[1]}). Возможно, Z нужно транспонировать?")

    interp_func = RegularGridInterpolator((x_coords, y_coords), z_values, method='linear', bounds_error=False,
                                          fill_value=None)

    target_z = float(interp_func(np.array([[target_x, target_y]]))[0])
    return target_z


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
    a1 = table1_data[0][0]
    x_coords1 = table1_data[1]
    y_coords1 = table1_data[2]
    z_values1 = table1_data[3]

    a2 = table2_data[0][0]
    z_values2 = table2_data[3]

    z1_at_xy = bilinear_interpolation([x_coords1, y_coords1, z_values1], target_x, target_y)
    print(f"Промежуточный Z1 (для A={a1}) при X={target_x}, Y={target_y}: {z1_at_xy:.3f}")

    z2_at_xy = bilinear_interpolation([x_coords1, y_coords1, z_values2], target_x,
                                      target_y)
    print(f"Промежуточный Z2 (для A={a2}) при X={target_x}, Y={target_y}: {z2_at_xy:.3f}")

    if a1 == a2:
        if target_a == a1:
            return z1_at_xy
        else:
            print(
                f"Предупреждение: a1 ({a1}) и a2 ({a2}) равны, но target_a ({target_a}) отличается. Возвращаем z1_at_xy.")
            return z1_at_xy

    a_values = np.array([a1, a2])
    z_for_a_interp = np.array([z1_at_xy, z2_at_xy])

    sort_indices_a = np.argsort(a_values)
    a_values_sorted = a_values[sort_indices_a]
    z_for_a_interp_sorted = z_for_a_interp[sort_indices_a]

    if not np.all(np.diff(a_values_sorted) > 0):
        raise ValueError("Значения A для линейной интерполяции должны быть различными.")

    interp_func_a = interp1d(a_values_sorted, z_for_a_interp_sorted, kind='linear', fill_value="extrapolate")
    final_z = float(interp_func_a(target_a))

    return final_z
