import math

def calculate_thermal_characteristics(params: dict) -> dict:
    A = params['A']
    Z = params['Z']
    FN = params['FN']
    DI = params['DI']
    DK = params['DK']
    DLCT = params['DLCT']
    BAP = params['BAP']
    DD = params['DD']
    DCT = params['DCT']
    W_lists = params['W']
    T1_lists = params['T1']
    D_list = params['D']
    R_list = params['R']
    RBETA_list = params['RBETA']
    GV = params['GV']

    Pi = math.pi
    W = [[0.0] * 3 for _ in range(11)]
    T1 = [[0.0] * 3 for _ in range(11)]
    D = [0.0] * 11
    R = [0.0] * 11
    RBETA = [0.0] * 11

    for i, val in enumerate(W_lists[0], 1): W[i][1] = val
    for i, val in enumerate(W_lists[1], 1): W[i][2] = val
    for i, val in enumerate(T1_lists[0], 1): T1[i][1] = val
    for i, val in enumerate(T1_lists[1], 1): T1[i][2] = val
    for i, val in enumerate(D_list, 1): D[i] = val
    for i, val in enumerate(R_list, 1): R[i] = val / 10**6
    for i, val in enumerate(RBETA_list, 1): RBETA[i] = val
    
    TMAX = len(T1_lists[0])
    LMAX = len(D_list)

    main_results = []
    
    FK = [0.0] * 3; WB = [0.0] * 3; DR = [0.0] * 3; FKT = [0.0] * 3
    T3 = [0.0] * 3; FKD = [0.0] * 3; T4 = [0.0] * 3; TC = [0.0] * 3
    T = [0.0] * 3

    n = BAP
    FK[1] = Pi * A[1] * FN[1] * (DD + 2.0 * DCT)
    FK[2] = Pi * A[2] * FN[2] * (DD + 2.0 * DCT) if n > 2 else 0.0
    
    fk_sum = FK[1] + FK[2]
    DKN = DK * 1000.0 / fk_sum if fk_sum != 0 else 0

    for i in range(1, len(W_lists[0]) + 1):
        if W[i][1] == 0: continue
        
        WB[1] = W[i][1] * Z[1] / (900.0 * Pi * FN[1] * DD**2) if (FN[1] * DD != 0) else 0.0
        if n > 2 and (FN[2] * DD != 0):
            WB[2] = W[i][2] * Z[2] / (900.0 * Pi * FN[2] * DD**2)
        else:
            WB[2] = 0.0
        
        for m in range(1, len(R_list) + 1):
            R1 = R[m]
            if R1 == 0: continue

            for J in range(1, TMAX + 1):
                if T1[J][1] == 0: continue
                
                for L in range(1, LMAX + 1):
                    DT = D[L]
                    if DT == 0.0: continue
                    
                    for nx in range(1, 3):
                        T[nx] = T1[J][nx]
                        B = 1.1 * WB[nx] / (DD * 1000.0)**0.25 if (WB[nx] * DD != 0) else 1.0
                        X = 0.12 * (1.0 + 0.15 * T[nx])
                        FW = B**X
                        FT = 1.0 - 0.42 * (35.0 - T[nx])**2 * 0.001
                        FZ = 1.0 + 0.1 * (Z[nx] - 2.0) * (1.0 - T[nx] / 35.0)
                        DR[nx] = (0.9 - 0.012 * T[nx]) * DKN
                        FKT[nx] = 3500.0 * FW * FT * FZ
                        
                        DKT = DT * 1000.0 / fk_sum if fk_sum != 0 else 0
                        R3 = DKT / DR[nx] if DR[nx] != 0 else float('inf')
                        FD = R3 * (2.0 - R3) if R3 < 1.0 else 1.0
                        FKT[nx] *= FD
                        
                        fkt_inv = 1.0 / FKT[nx] if FKT[nx] != 0 else float('inf')
                        term2 = (DCT / DLCT - 0.001 / 90.0) if DLCT != 0 else float('inf')
                        FKT[nx] = 1.0 / (fkt_inv + term2) if not math.isinf(fkt_inv + term2) else 0

                        if n <= 2: break

                    T3 = [0.0] * 3
                    DKT_for_T3 = D[L] * 1000.0 / fk_sum if fk_sum != 0 else 0
                    if W[i][1] != 0:
                        T3[1] = (DKT_for_T3 * FK[1] * DI) / (W[i][1] * 1000.0)
                    if W[i][2] != 0 and n > 2:
                         T3[2] = (DKT_for_T3 * FK[2] * DI) / (W[i][2] * 1000.0)

                    solved = False
                    if n > 2:
                        SHET, DELTA = 0.0, 0.1
                        for _ in range(100):
                            for nx_calc in range(1, 3):
                                fkd_inv = 1.0 / FKT[nx_calc] if FKT[nx_calc] != 0 else float('inf')
                                FKD[nx_calc] = 1.0 / (fkd_inv + R1) if (fkd_inv + R1) != 0 else 0
                                
                                exp_arg = (FKD[nx_calc] * FK[nx_calc]) / (W[i][nx_calc] * 1000.0) if W[i][nx_calc] != 0 else float('inf')
                                try: exp_val = math.exp(exp_arg)
                                except OverflowError: exp_val = float('inf')
                                    
                                T4[nx_calc] = T3[nx_calc] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0
                                TC[nx_calc] = T[nx_calc] + T3[nx_calc] + T4[nx_calc]
                            
                            T2 = TC[1] - TC[2]
                            if SHET * T2 < 0: DELTA /= 5.0
                            SHET = T2
                            
                            if abs(T2) <= 0.01:
                                solved = True; break

                            T3[1] += DELTA if T2 < 0 else -DELTA
                            if W[i][2] != 0:
                                T3[2] = (D[L] * DI - T3[1] * W[i][1]) / W[i][2]
                            else:
                                solved = True; break
                    else:
                        nx = 1
                        fkd_inv = 1.0 / FKT[nx] if FKT[nx] != 0 else float('inf')
                        FKD[nx] = 1.0 / (fkd_inv + R1) if (fkd_inv + R1) != 0 else 0
                        exp_arg = (FKD[nx] * FK[nx]) / (W[i][nx] * 1000.0) if W[i][nx] != 0 else float('inf')
                        try: exp_val = math.exp(exp_arg)
                        except OverflowError: exp_val = float('inf')
                        T4[nx] = T3[nx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                        TC[nx] = T[nx] + T3[nx] + T4[nx]
                        FKD[2], T3[2], T4[2], TC[2] = 0.0, 0.0, 0.0, 0.0
                        solved = True

                    if solved:
                        TK = TC[1]
                        G = TK + 273.15
                        try:
                            log_G = math.log(G)
                            ps_exp = 82.86568 + 1.028003 / 100.0 * G - 7821.541 / G - 11.48776 * log_G
                            PS = math.exp(ps_exp) / 0.0981
                        except (ValueError, ZeroDivisionError):
                            PS = 0
                        
                        main_results.append({
                            "W1": W[i][1], "W2": W[i][2], "R_input": R_list[m-1], "Beta": RBETA[m-1],
                            "D": DT, "T1_1": T1[J][1], "T1_2": T1[J][2],
                            "R_calc": R1 * 10**6, "FKD1": FKD[1], "FKD2": FKD[2],
                            "T3_1": T3[1], "T3_2": T3[2], "T4_1": T4[1], "T4_2": T4[2],
                            "TK": TK, "PS": PS
                        })

    ejector_results = {'temps': [], 'pk_values_1': [], 'pk_values_2': []}
    if GV > 0:
        temps_rev = T1_lists[0][::-1]
        ejector_results['temps'] = temps_rev
        
        for k in range(1, 3):
            pk_values = []
            for temp_val in temps_rev:
                TT = temp_val + 273.15 + 1.0
                TS = TT / 1000.0
                try:
                    ps_exp = -7.821541 / TS + 82.86586 + 10.28 * TS - 11.48776 * math.log(TT)
                    PS_ejector = math.exp(ps_exp)
                    PK = (0.009 + 0.0003 * GV / k + PS_ejector * 10) * 100
                except (ValueError, ZeroDivisionError): PK = 0
                pk_values.append(PK)
            
            if k == 1: ejector_results['pk_values_1'] = pk_values
            if k == 2: ejector_results['pk_values_2'] = pk_values

    return {'main_results': main_results, 'ejector_results': ejector_results}