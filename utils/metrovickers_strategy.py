import math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Any

class MetroVickersStrategy:
    def __init__(self):
        k_interpolation_data = {
            "temperature_points": [5, 15, 27, 38, 50, 70, 95, 120, 150],  # Средняя температура tср [°C]
            "speed_points": [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6], # Скорость воды Cов [м/с]
            "k_values_matrix": [
                [800, 1050, 1260, 1430, 1540, 1670, 1770, 1870, 1930],
                [1260, 1510, 1720, 1890, 2000, 2170, 2270, 2370, 2430],
                [1670, 1920, 2130, 2300, 2430, 2600, 2700, 2800, 2860],
                [1970, 2220, 2450, 2620, 2750, 2950, 3060, 3160, 3230],
                [2200, 2450, 2680, 2850, 2990, 3190, 3290, 3390, 3490],
                [2410, 2680, 2900, 3080, 3210, 3400, 3520, 3620, 3700],
                [2590, 2840, 3070, 3230, 3380, 3570, 3690, 3790, 3880],
                [2760, 3010, 3230, 3420, 3550, 3730, 3850, 3960, 4040],
                [2830, 3080, 3300, 3490, 3630, 3810, 3930, 4040, 4120],
                [2900, 3150, 3370, 3570, 3700, 3870, 4000, 4110, 4190],
                [2980, 3230, 3440, 3640, 3770, 3950, 4070, 4180, 4250],
                [3040, 3290, 3500, 3690, 3830, 4000, 4120, 4220, 4310],
                [3150, 3400, 3620, 3810, 3940, 4120, 4230, 4350, 4420],
                [3250, 3500, 3710, 3910, 4040, 4220, 4330, 4440, 4540],
                [3340, 3590, 3800, 3990, 4130, 4320, 4420, 4530, 4610],
                [3440, 3690, 3870, 4050, 4180, 4390, 4500, 4600, 4670],
                [3500, 3750, 3930, 4100, 4230, 4460, 4560, 4660, 4730],
                [3560, 3810, 3990, 4160, 4290, 4520, 4620, 4720, 4790],
                [3600, 3850, 4040, 4200, 4340, 4560, 4660, 4760, 4840]
            ]
        }
        self._get_k_from_table = RegularGridInterpolator(
            (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
            np.array(k_interpolation_data["k_values_matrix"]),
            bounds_error=False,
            fill_value=None
        )
        
        # Константы
        self.coefficient_B_const = 0.974
        self.temperature_cooling_water_average_heating_const = 25.0  # °С
        self.speed_cooling_water_const = 2.0  # м/с
        
        self._get_heat_of_vaporization = lambda temp: (30 - temp) * 0.582 + 580.4
        self._get_pressure_from_saturation_temp = lambda temp: (0.0001 * temp**2 + 0.0016*temp + 0.04) * 0.980665

    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        diameter_inside_of_pipes = params['diameter_inside_of_pipes']
        thickness_pipe_wall = params['thickness_pipe_wall']
        length_cooling_tubes_of_the_main_bundle = params['length_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_main_bundle = params['number_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_built_in_bundle = params['number_cooling_tubes_of_the_built_in_bundle']
        number_cooling_water_passes_of_the_main_bundle = params['number_cooling_water_passes_of_the_main_bundle']
        mass_flow_cooling_water = params['mass_flow_cooling_water']
        temperature_cooling_water_1 = params['temperature_cooling_water_1']
        thermal_conductivity_cooling_surface_tube_material = params['thermal_conductivity_cooling_surface_tube_material']
        coefficient_b = params.get('coefficient_b', 1.0)
        mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
        degree_dryness_flow_path_1 = params['degree_dryness_flow_path_1']
        
        number_air_cooler_total_pipes = params.get('number_air_cooler_total_pipes')
        if number_air_cooler_total_pipes is None:
            number_air_cooler_total_pipes = (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) * 0.15

        results = {}

        diameter_outside_of_pipes = diameter_inside_of_pipes + 2 * thickness_pipe_wall
        results['diameter_outside_of_pipes'] = diameter_outside_of_pipes

        area_tube_bundle_surface_total = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                          (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) *
                                          diameter_outside_of_pipes * 1e-6)
        results['area_tube_bundle_surface_total'] = area_tube_bundle_surface_total
        
        area_surface_of_the_air_cooler_tube_bundle = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                                      number_air_cooler_total_pipes *
                                                      diameter_outside_of_pipes * 1e-6)
        results['area_surface_of_the_air_cooler_tube_bundle'] = area_surface_of_the_air_cooler_tube_bundle
        
        if area_surface_of_the_air_cooler_tube_bundle == 0:
            coefficient_Kf = 1.0
        else:
            coefficient_Kf = 1 - 0.225 * (area_tube_bundle_surface_total / area_surface_of_the_air_cooler_tube_bundle)
        results['coefficient_Kf'] = coefficient_Kf
        
        coefficient_R1 = ((2 * thickness_pipe_wall * diameter_outside_of_pipes) /
                          ((diameter_outside_of_pipes + diameter_inside_of_pipes) * thermal_conductivity_cooling_surface_tube_material))
        results['coefficient_R1'] = coefficient_R1

        speed_cooling_water = ((mass_flow_cooling_water * number_cooling_water_passes_of_the_main_bundle) /
                               (900 * math.pi * (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) *
                                (diameter_inside_of_pipes / 1000)**2))
        results['speed_cooling_water'] = speed_cooling_water

        coefficient_K_temp = self._get_k_from_table((self.speed_cooling_water_const, self.temperature_cooling_water_average_heating_const)).item()
        results['coefficient_K_temp'] = coefficient_K_temp

        k_clean_denominator = (1 / (coefficient_K_temp * 0.85 * self.coefficient_B_const * coefficient_Kf)) - 0.087 / 10000 + coefficient_R1
        coefficient_K = 1 / k_clean_denominator
        results['coefficient_K'] = coefficient_K

        coefficient_R = (1 / coefficient_K) * ((1 / coefficient_b) - 1)
        results['coefficient_R'] = coefficient_R

        heat_of_vaporization = self._get_heat_of_vaporization(temperature_cooling_water_1)
        results['heat_of_vaporization'] = heat_of_vaporization
        
        delta_t_water = (mass_flow_flow_path_1 * heat_of_vaporization * degree_dryness_flow_path_1) / mass_flow_cooling_water
        temperature_cooling_water_2 = temperature_cooling_water_1 + delta_t_water
        results['temperature_cooling_water_2'] = temperature_cooling_water_2
        
        temperature_cooling_water_average_heating = (temperature_cooling_water_1 + temperature_cooling_water_2) / 2
        results['temperature_cooling_water_average_heating'] = temperature_cooling_water_average_heating

        k_zag_denominator = (1 / (coefficient_K_temp * 0.85 * self.coefficient_B_const * coefficient_Kf)) - 0.087 / 10000 + coefficient_R1 + coefficient_R
        coefficient_Kzag = 1 / k_zag_denominator
        results['coefficient_Kzag'] = coefficient_Kzag

        water_heat_capacity_rate = (mass_flow_cooling_water * 1000 / 3600) * 4186.8 # Вт/К
        
        exponent_val = (coefficient_Kzag * area_tube_bundle_surface_total) / water_heat_capacity_rate
        
        if exponent_val > 700:
            temperature_relative_underheating = 0
        else:
            temperature_relative_underheating = (temperature_cooling_water_2 - temperature_cooling_water_1) / (math.exp(exponent_val) - 1)
        results['temperature_relative_underheating'] = temperature_relative_underheating
        
        temperature_saturation_steam = temperature_cooling_water_2 + temperature_relative_underheating
        results['temperature_saturation_steam'] = temperature_saturation_steam

        pressure_flow_path_1 = self._get_pressure_from_saturation_temp(temperature_saturation_steam)
        results['pressure_flow_path_1'] = pressure_flow_path_1

        return results