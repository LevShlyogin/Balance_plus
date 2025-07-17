import math

class MetroVickersStrategy:
    def __init__(self, params: dict):
        self.d_inside = params['diameter_inside_of_pipes']
        self.s_wall = params['thickness_pipe_wall']
        self.L_act = params['length_cooling_tubes_of_the_main_bundle']
        self.N_op = params['number_cooling_tubes_of_the_main_bundle']
        self.N_vp = params.get('number_cooling_tubes_of_the_built-in_bundle', 0)
        self.Z_op = params['number_cooling_water_passes_of_the_main_bundle']
        self.lambda_material = params['thermal_conductivity_cooling_surface_tube_material']
        self.material_name = params.get('material_name', "не указан")
        self.temp_axis = params['vik_table_temps']
        self.speed_axis = params['vik_table_speeds']
        self.k_values_table = params['vik_table_k_values']
        self.coefficient_B_const = 0.974
        self.VAR = params['VAR']

        if 'number_air_cooler_total_pipes' in params:
            self.N_vo = params['number_air_cooler_total_pipes']
        else:
            self.N_vo = (self.N_op + self.N_vp) * 0.15

        self.d_outside = self.d_inside + 2 * self.s_wall
        self.F_total = math.pi * self.L_act * (self.N_op + self.N_vp) * self.d_outside
        self.F_vo = math.pi * self.L_act * self.N_vo * self.d_outside
        self.Kf = 1.0 - 0.225 * (self.F_vo / self.F_total) if self.F_total > 0 else 1.0

        denominator = (self.d_outside + self.d_inside) * self.lambda_material
        self.R1 = (2 * self.s_wall * self.d_outside) / denominator if denominator > 0 else float('inf')

        if self.VAR == 1:
            VS_ref = self._get_k_from_table(2.5, 75.0)
        else:
            VS_ref = self._get_k_from_table(2.0, 25.0)

        term1 = 1.0 / (VS_ref * 0.85 * self.coefficient_B_const * self.Kf) if (VS_ref * self.coefficient_B_const * self.Kf) != 0 else float('inf')
        term2 = 0.087 / 10000.0
        inv_vsr = term1 - term2 + self.R1
        self.vsr = 1.0 / inv_vsr if inv_vsr != 0 else 0.0

    def _get_k_from_table(self, speed: float, temp: float) -> float:
        if not (self.speed_axis[0] <= speed <= self.speed_axis[-1]): return 0.0
        k = 0
        while k < len(self.speed_axis) and self.speed_axis[k] < speed: k += 1
        if k > 0 and self.speed_axis[k-1] == speed: k -= 1
        
        if not (self.temp_axis[0] <= temp <= self.temp_axis[-1]): return 0.0
        L = 0
        while L < len(self.temp_axis) and self.temp_axis[L] < temp: L += 1
        if L > 0 and self.temp_axis[L-1] == temp: L -= 1

        k0, k1 = max(0, k - 1), k
        L0, L1 = max(0, L - 1), L
        
        if k1 >= len(self.speed_axis) or L1 >= len(self.temp_axis): return 0.0

        K_k0_L0 = self.k_values_table[k0][L0]; K_k1_L0 = self.k_values_table[k1][L0]
        K_k0_L1 = self.k_values_table[k0][L1]; K_k1_L1 = self.k_values_table[k1][L1]
        
        d = self.speed_axis[k1] - self.speed_axis[k0]
        r = speed - self.speed_axis[k0]
        dd = self.temp_axis[L1] - self.temp_axis[L0]
        rr = temp - self.temp_axis[L0]
        
        if d == 0 or dd == 0: return K_k0_L0

        k_val = (K_k0_L0 * (d - r) * (dd - rr) + K_k1_L0 * r * (dd - rr) +
                 K_k0_L1 * (d - r) * rr + K_k1_L1 * r * rr) / (d * dd)
        return k_val

    def calculate_relative_underheating(self, mass_flow: float, avg_temp: float, beta_coeff: float) -> float:
        if self.vsr == 0 or beta_coeff == 0:
            fouling_resistance_RZ = float('inf')
        else:
            fouling_resistance_RZ = (1.0 / self.vsr) * (1.0 / beta_coeff - 1.0)
            
        denominator = 900 * math.pi * (self.N_op + self.N_vp) * self.d_inside**2
        speed_cooling_water = (mass_flow * self.Z_op) / denominator if denominator > 0 else 0
        
        K_from_table = self._get_k_from_table(speed_cooling_water, avg_temp)
        if K_from_table == 0: return None

        term_k_table = K_from_table * 0.85 * self.coefficient_B_const * self.Kf
        if term_k_table == 0: return None
        
        inv_K_fouled = (1 / term_k_table) - 0.000087 + self.R1 + fouling_resistance_RZ
        
        if inv_K_fouled <= 0: return None
        K_fouled = 1.0 / inv_K_fouled
        
        exp_denominator = mass_flow * 1000
        if exp_denominator == 0: return float('inf')

        try:
            exp_argument = (K_fouled * self.F_total) / exp_denominator
            exp_val = math.exp(exp_argument)
            relative_underheating = 1.0 / (exp_val - 1.0)
        except (OverflowError, ZeroDivisionError):
            relative_underheating = 0.0

        return relative_underheating