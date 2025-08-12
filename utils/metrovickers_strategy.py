import math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Any
from iapws import IAPWS97

from utils.Constants import coefficient_B_const, temperature_cooling_water_average_heating_const, speed_cooling_water_const, k_interpolation_data

class MetroVickersStrategy:
    def __init__(self):
        self._get_k_from_table = RegularGridInterpolator(
            (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
            np.array(k_interpolation_data["k_values_matrix"]),
            bounds_error=False,
            fill_value=None
        )
        
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
                                          number_cooling_tubes_of_the_main_bundle * 
                                          diameter_outside_of_pipes * 1e-6)
        results['area_tube_bundle_surface_total'] = area_tube_bundle_surface_total

        area_surface_of_the_air_cooler_tube_bundle = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                                      number_air_cooler_total_pipes *
                                                      diameter_outside_of_pipes * 1e-6)
        results['area_surface_of_the_air_cooler_tube_bundle'] = area_surface_of_the_air_cooler_tube_bundle
        
        if area_surface_of_the_air_cooler_tube_bundle == 0:
            coefficient_Kf = 1.0
        else:
            coefficient_Kf = 1 - 0.225 * (area_surface_of_the_air_cooler_tube_bundle / area_tube_bundle_surface_total)
        results['coefficient_Kf'] = coefficient_Kf
        
        coefficient_R1 = ((2 * thickness_pipe_wall / 1000 * diameter_outside_of_pipes / 1000) / 
                          ((diameter_outside_of_pipes / 1000 + diameter_inside_of_pipes / 1000) 
                           * thermal_conductivity_cooling_surface_tube_material))
        results['coefficient_R1'] = coefficient_R1

        temperature_saturation_steam_prev = 0
        max_iterations = 20
        tolerance = 0.001

        speed_cooling_water = ((mass_flow_cooling_water * number_cooling_water_passes_of_the_main_bundle) /
                               (900 * math.pi * (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) *
                                (diameter_inside_of_pipes / 1000)**2))
        results['speed_cooling_water'] = speed_cooling_water

        heat_of_vaporization = self._get_heat_of_vaporization(temperature_cooling_water_1)
        results['heat_of_vaporization'] = heat_of_vaporization
        
        delta_t_water = (mass_flow_flow_path_1 * heat_of_vaporization * degree_dryness_flow_path_1) / mass_flow_cooling_water
        temperature_cooling_water_2 = temperature_cooling_water_1 + delta_t_water
        results['temperature_cooling_water_2'] = temperature_cooling_water_2
        
        temperature_cooling_water_average_heating = (temperature_cooling_water_1 + temperature_cooling_water_2) / 2
        results['temperature_cooling_water_average_heating'] = temperature_cooling_water_average_heating

        for _ in range(max_iterations):
            coefficient_K_temp = self._get_k_from_table((speed_cooling_water_const, temperature_cooling_water_average_heating_const)).item()

            k_clean_denominator = (1 / (coefficient_K_temp * 0.85 * coefficient_B_const * coefficient_Kf)) - 0.087 / 10000 + coefficient_R1
            coefficient_K = 1 / k_clean_denominator

            coefficient_R = (1 / coefficient_K) * ((1 / coefficient_b) - 1)

            k_zag_denominator = (1 / (coefficient_K_temp * 0.85 * coefficient_B_const * coefficient_Kf)) - 0.087 / 10000 + coefficient_R1 + coefficient_R
            coefficient_Kzag = 1 / k_zag_denominator
        
            exponent_val = (coefficient_Kzag * area_tube_bundle_surface_total) / (mass_flow_cooling_water * 1000)
            
            if exponent_val > 700:
                temperature_relative_underheating = 0
            else:
                temperature_relative_underheating = (1 / (math.exp(exponent_val) - 1))
        
            temperature_saturation_steam = temperature_cooling_water_2 + temperature_relative_underheating

            if abs(temperature_saturation_steam - temperature_saturation_steam_prev) < tolerance:
                break

            temperature_saturation_steam_prev = temperature_saturation_steam

        results['coefficient_K_temp'] = coefficient_K_temp
        results['coefficient_K'] = coefficient_K
        results['coefficient_R'] = coefficient_R
        results['coefficient_Kzag'] = coefficient_Kzag
        results['temperature_relative_underheating'] = temperature_relative_underheating
        results['temperature_saturation_steam'] = temperature_saturation_steam

        # pressure_flow_path_1 = self._get_pressure_from_saturation_temp(temperature_saturation_steam)

        sat_steam = IAPWS97(T=temperature_saturation_steam + 273.15, x=1)
        pressure_flow_path_1_mpa = sat_steam.P
        pressure_flow_path_1_kgf_cm2 = pressure_flow_path_1_mpa * 10.197
        results['pressure_flow_path_1'] = pressure_flow_path_1_kgf_cm2

        return results