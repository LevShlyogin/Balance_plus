from typing import Dict, Any, List
import numpy as np
from scipy import interpolate

class TablePressureStrategy:    
    def _create_namet_interpolator(self, namet_data: List) -> interpolate.RectBivariateSpline:
        t_axis_raw = np.array(namet_data[0])
        g_axis = np.array(namet_data[1])
        values_raw = np.array(namet_data[2])

        if np.all(np.diff(t_axis_raw) < 0):
            t_axis = t_axis_raw[::-1]
            values = values_raw[::-1, :]
        else:
            t_axis = t_axis_raw
            values = values_raw
            
        num_t_points = len(t_axis)
        num_g_points = len(g_axis)

        kx = min(num_t_points - 1, 3)
        ky = min(num_g_points - 1, 3)
        
        return interpolate.RectBivariateSpline(t_axis, g_axis, values, kx=kx, ky=ky)

    def _create_named_interpolator(self, named_data: List) -> interpolate.interp1d:
        t_axis = np.array(named_data[0])
        p_axis = np.array(named_data[1])
        
        return interpolate.interp1d(t_axis, p_axis, bounds_error=False, fill_value="extrapolate")

    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        temperature_cooling_water_1 = params['temperature_cooling_water_1']
        mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
        namet_data = params['NAMET']
        named_data = params['NAMED']

        named_interpolator = self._create_named_interpolator(named_data)
        pressure_flow_path_1_NAMED = named_interpolator(temperature_cooling_water_1)
        
        namet_interpolator = self._create_namet_interpolator(namet_data)
        pressure_flow_path_1_NAMET = namet_interpolator(
            temperature_cooling_water_1, 
            mass_flow_flow_path_1
        )[0][0]
        
        if pressure_flow_path_1_NAMET >= pressure_flow_path_1_NAMED:
            pressure_flow_path_1 = pressure_flow_path_1_NAMET
        else:
            pressure_flow_path_1 = float(pressure_flow_path_1_NAMED)

        return {
            'pressure_flow_path_1_NAMET': pressure_flow_path_1_NAMET,
            'pressure_flow_path_1_NAMED': float(pressure_flow_path_1_NAMED),
            'pressure_flow_path_1': pressure_flow_path_1
        }