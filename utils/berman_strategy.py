import math

class BermanStrategy():
    def calculate(self, params: dict) -> dict:
        A = [0.0] * 3
        A[1] = params['length_cooling_tubes_of_the_main_bundle']
        A[2] = params.get('length_cooling_tubes_of_the_built_in_bundle', 0.0)

        Z = [0] * 3
        Z[1] = params['number_cooling_water_passes_of_the_main_bundle']
        Z[2] = params.get('number_cooling_water_passes_of_the_built_in_bundle', 0)

        FN = [0] * 3
        FN[1] = params['number_cooling_tubes_of_the_main_bundle']
        FN[2] = params.get('number_cooling_tubes_of_the_built_in_bundle', 0)

        DI = params['enthalpy_flow_path_1'] 
        DK = params['mass_flow_steam_nom'] 
        DLCT = params['thermal_conductivity_cooling_surface_tube_material'] 
        BAP = params.get('BAP', 1) 
        DD = params['diameter_inside_of_pipes'] / 1000.0 
        DCT = params['thickness_pipe_wall'] / 1000.0 

        W_lists = [params['mass_flow_cooling_water_list'], params.get('mass_flow_cooling_water_built_in_beam_list', [])]
        T1_lists = [params['temperature_cooling_water_1_list'], params.get('temperature_cooling_water_built_in_beam_1_list', [])]
        D_list = params['mass_flow_steam_list']
        R_list = params['coefficient_R_list']
        
        GV = params.get('mass_flow_air', 0)
        
        W = [[0.0] * 3 for _ in range(11)]
        T1 = [[0.0] * 3 for _ in range(11)]
        D = [0.0] * 11
        R = [0.0] * 11

        for i, val in enumerate(W_lists[0], 1): W[i][1] = val
        if len(W_lists) > 1 and W_lists[1]:
            for i, val in enumerate(W_lists[1], 1): W[i][2] = val
        
        TMAX = 0
        for i, val in enumerate(T1_lists[0], 1):
            T1[i][1] = val
            if val != 0: TMAX = i
        if len(T1_lists) > 1 and T1_lists[1]:
            for i, val in enumerate(T1_lists[1], 1): T1[i][2] = val

        LMAX = 0
        for i, val in enumerate(D_list, 1):
            D[i] = val
            if val != 0: LMAX = i
            
        for i, val in enumerate(R_list, 1):
            R[i] = val 

        main_results = []
        pi = math.pi
        n = BAP

        WB = [0.0] * 3; DR = [0.0] * 3; FKT = [0.0] * 3
        T3_calc = [0.0] * 3; FKD = [0.0] * 3; T4 = [0.0] * 3; TC = [0.0] * 3; T_calc = [0.0] * 3
        
        FK = [0.0] * 3
        FK[1] = pi * A[1] * FN[1] * (DD + 2.0 * DCT)
        FK[2] = pi * A[2] * FN[2] * (DD + 2.0 * DCT) if n > 2 else 0.0
        
        total_area = FK[1] + FK[2]
        DKN = DK * 1000.0 / total_area if total_area != 0 else 0.0

        for i in range(1, len(W_lists[0]) + 1):
            if W[i][1] == 0: break

            if FN[1] > 0 and DD > 0:
                WB[1] = W[i][1] * Z[1] / (900.0 * pi * FN[1] * DD**2)
            else:
                WB[1] = 0.0
            
            if n > 2 and FN[2] > 0 and DD > 0:
                WB[2] = W[i][2] * Z[2] / (900.0 * pi * FN[2] * DD**2)
            else:
                WB[2] = 0.0
            
            for m in range(1, len(R_list) + 1):
                R1 = R[m]
                if R1 == 0 and m > 1: break

                for J in range(1, TMAX + 1):
                    if T1[J][1] == 0: break
                    
                    for L in range(1, LMAX + 1):
                        DT = D[L]
                        if DT == 0: break
                        
                        T3_calc[1], T3_calc[2] = 0.0, 0.0

                        for k_loop_once in range(1):
                            for nx in range(1, 3):
                                T_calc[nx] = T1[J][nx] + T3_calc[nx]
                                if WB[nx] > 0 and DD > 0:
                                    B = 1.1 * WB[nx] / (DD * 1000.0)**0.25
                                    X = 0.12 * (1.0 + 0.15 * T_calc[nx])
                                    FW = B**X
                                else:
                                    FW = 1.0
                                
                                FT = 1.0 - 0.42 * (35.0 - T_calc[nx])**2 * 0.001
                                FZ = 1.0 + 0.1 * (Z[nx] - 2.0) * (1.0 - T_calc[nx] / 35.0)
                                DR[nx] = (0.9 - 0.012 * T_calc[nx]) * DKN
                                FKT[nx] = 3500.0 * FW * FT * FZ
                                if n <= 2: break
                            
                            for nx in range(1, 3):
                                DKT = DT * 1000.0 / total_area if total_area != 0 else 0.0
                                R3 = DKT / DR[nx] if DR[nx] != 0 else float('inf')
                                FD = R3 * (2.0 - R3) if R3 < 1.0 else 1.0
                                FKT[nx] *= FD
                                
                                k_inv = 1.0 / FKT[nx] if FKT[nx] != 0 else float('inf')
                                term2 = (DCT / DLCT - 0.001 / 90.0) if DLCT != 0 else float('inf')
                                FKT[nx] = 1.0 / (k_inv + term2) if not math.isinf(k_inv + term2) else 0.0
                                
                                dkt_fk = DKT * FK[nx]
                                T3_calc[nx] = dkt_fk * DI / (W[i][nx] * 1000.0) if W[i][nx] > 0 else 0.0
                                
                                if n <= 2: break

                        if n > 2:
                            SHET, DELTA = 0.0, 0.1
                            for _ in range(100):
                                for nx in range(1, 3):
                                    k_inv = 1.0 / FKT[nx] if FKT[nx] != 0 else float('inf')
                                    FKD[nx] = 1.0 / (k_inv + R1)
                                    
                                    exp_arg = (FKD[nx] / W[i][nx] * FK[nx] / 1000.0) if W[i][nx] > 0 else float('inf')
                                    try: exp_val = math.exp(exp_arg)
                                    except OverflowError: exp_val = float('inf')
                                    
                                    T4[nx] = T3_calc[nx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                                    TC[nx] = T1[J][nx] + T3_calc[nx] + T4[nx] 

                                T2 = TC[1] - TC[2]
                                if SHET * T2 < 0: DELTA /= 5.0
                                SHET = T2
                                if abs(T2) <= 0.01: break
                                
                                T3_calc[1] += -DELTA if T2 > 0 else DELTA
                                if W[i][2] > 0:
                                    T3_calc[2] = (D[L] * DI - T3_calc[1] * W[i][1]) / W[i][2]
                                else:
                                    break
                            
                            TK = TC[1]

                        else:
                            nx = 1
                            k_inv = 1.0 / FKT[nx] if FKT[nx] != 0 else float('inf')
                            FKD[nx] = 1.0 / (k_inv + R1)
                            
                            exp_arg = (FKD[nx] / W[i][nx] * FK[nx] / 1000.0) if W[i][nx] > 0 else float('inf')
                            try: exp_val = math.exp(exp_arg)
                            except OverflowError: exp_val = float('inf')
                                
                            T4[nx] = T3_calc[nx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                            TK = T1[J][nx] + T3_calc[nx] + T4[nx]

                        G = TK + 273.15
                        try:
                            ps_exp = 82.86568 + 1.028003 / 100.0 * G - 7821.541 / G - 11.48776 * math.log(G)
                            pressure_condenser_Pa = math.exp(ps_exp)
                        except (ValueError, ZeroDivisionError):
                            pressure_condenser_Pa = 0.0
                        
                        main_results.append({
                            "pressure_condenser_Pa": pressure_condenser_Pa,
                            "temperature_saturation": TK,
                            "undercooling_main": T4[1],
                            "undercooling_built_in": T4[2],
                        })

        ejector_results = []
        if GV > 0:
            for k_ejector in range(1, 3):
                for n_t in range(1, TMAX + 1):
                    n1 = TMAX - n_t + 1
                    TT = T1[n1][1] + 273.15 + 1.0
                    TS = TT / 1000.0
                    try:
                        ps_ejector_Pa = math.exp(-7.821541 / TS + 82.86586 + 10.28 * TS - 11.48776 * math.log(TT))
                        pressure_ejector_kPa = (0.009 + 0.0003 * GV / k_ejector + ps_ejector_Pa * 10) * 100
                        
                        ejector_results.append({
                            "number_of_ejectors": k_ejector,
                            "inlet_water_temperature": T1[n1][1],
                            "ejector_pressure_kPa": pressure_ejector_kPa
                        })
                    except (ValueError, ZeroDivisionError):
                        pass

        return {'main_results': main_results, 'ejector_results': ejector_results}