import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Any

from utils.Constants import _P_DATA, _TVOZD_CONST_DEFAULT

class VKUStrategy:
    """
    Класс для расчета давления в воздушно-конденсационной установке (ВКУ).
    Методика основана на определении давления по приведенному расходу пара
    и температуре наружного воздуха с использованием 2D-интерполяции.
    """
    def __init__(self, mass_flow_steam_nom: float, degree_dryness_steam_nom: float):
        if mass_flow_steam_nom <= 0:
            raise ValueError("Номинальный расход пара (mass_flow_steam_nom) должен быть больше нуля.")
        if not (0 < degree_dryness_steam_nom <= 1):
            raise ValueError("Номинальная степень сухости (degree_dryness_steam_nom) должна быть в диапазоне (0, 1].")

        self.mass_flow_steam_nom = mass_flow_steam_nom
        self.degree_dryness_steam_nom = degree_dryness_steam_nom
        
        self._interpolator = self._create_interpolator()

    def _create_interpolator(self) -> RegularGridInterpolator:
        t_air_axis_desc = np.array(_P_DATA[0])
        g_reduced_axis = np.array(_P_DATA[1])
        p_values = np.array(_P_DATA[2])

        if t_air_axis_desc[0] > t_air_axis_desc[-1]:
            t_air_axis_asc = np.flip(t_air_axis_desc)
            p_values_reordered = np.fliplr(p_values)
        else:
            t_air_axis_asc = t_air_axis_desc
            p_values_reordered = p_values

        return RegularGridInterpolator(
            (g_reduced_axis, t_air_axis_asc), 
            p_values_reordered,
            bounds_error=False,
            fill_value=None
        )

    def calculate(self, params: Dict[str, Any]) -> Dict[str, float]:
        """
        Выполняет расчет давления в конденсаторе.

        Args:
            params (Dict[str, Any]): Словарь с входными параметрами.
                Обязательные ключи:
                - 'mass_flow_flow_path_1' (float): G1, текущий расход пара [т/ч].
                - 'degree_dryness_flow_path_1' (float): X1, текущая степень сухости.
                Опциональный ключ:
                - 'temperature_air' (float): tвозд, температура наружного воздуха [°C].

        Returns:
            Dict[str, float]: Словарь с результатами расчета.
                - 'pressure_flow_path_1': P1, рассчитанное давление в конденсаторе [кгс/см²].
                - 'mass_flow_reduced_steam_condencer': Gк_прив, приведенный расход [%].
        
        Raises:
            KeyError: Если в словаре `params` отсутствует обязательный ключ.
        """
        try:
            mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
            degree_dryness_flow_path_1 = params['degree_dryness_flow_path_1']
        except KeyError as e:
            raise KeyError(f"Отсутствует обязательный параметр в словаре: {e}")

        t_air = params.get('temperature_air', _TVOZD_CONST_DEFAULT)

        mass_flow_reduced_steam_condencer = (
            (mass_flow_flow_path_1 / self.mass_flow_steam_nom) *
            (degree_dryness_flow_path_1 / self.degree_dryness_steam_nom) * 100
        )

        point_to_interpolate = (mass_flow_reduced_steam_condencer, t_air)
        pressure_flow_path_1 = self._interpolator(point_to_interpolate).item()

        results = {
            'pressure_flow_path_1': pressure_flow_path_1,
            'mass_flow_reduced_steam_condencer': mass_flow_reduced_steam_condencer
        }

        return results