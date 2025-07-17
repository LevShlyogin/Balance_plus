from utils.berman_strategy import BermanStrategy

def create_markdown_table(headers, rows):
    header_line = "| " + " | ".join(map(str, headers)) + " |"
    separator_line = "|:---" + "|---:".join([""] * len(headers)) + "|"
    
    row_lines = []
    for row in rows:
        formatted_row = [row[0]] + [f"{val:.3f}" for val in row[1:]]
        row_lines.append("| " + " | ".join(map(str, formatted_row)) + " |")
        
    return "\n".join([header_line, separator_line] + row_lines)

def run_simulation(wo, wbc, b_label, r_raw_value, has_ejector_data):
    r_old_units = r_raw_value / 1_000_000
    r_si_units = r_old_units / 860
    
    base_params = {
        'length_cooling_tubes_of_the_main_bundle': 7.080,
        'number_cooling_water_passes_of_the_main_bundle': 2,
        'number_cooling_tubes_of_the_main_bundle': 1754,
        'enthalpy_flow_path_1': 2175.68, 
        'mass_flow_steam_nom': 16.00,
        'thermal_conductivity_cooling_surface_tube_material': 37.0,
        'diameter_inside_of_pipes': 22.0,
        'thickness_pipe_wall': 1.0,
        
        'coefficient_R_list': [r_si_units],
        
        'temperature_cooling_water_1_list': [4, 5, 10, 15, 20, 25, 30, 35],
        'mass_flow_steam_list': [16, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'mass_flow_cooling_water_list': [wo], 
        'mass_flow_cooling_water_built_in_beam_list': [wbc],
        'BAP': float(b_label) if b_label != ".75" else 0.75,
        'mass_flow_air': 16.5 if has_ejector_data else 0.0,
        'length_cooling_tubes_of_the_built_in_bundle': 0.0,
        'number_cooling_water_passes_of_the_built_in_bundle': 0,
        'number_cooling_tubes_of_the_built_in_bundle': 0,
        'temperature_cooling_water_built_in_beam_1_list': [0] * 8,
    }

    strategy = BermanStrategy()
    results = strategy.calculate(base_params)

    ejector_table_str = ""
    if has_ejector_data and results['ejector_results']:
        ejector_res = results['ejector_results']
        temps = sorted(list(set(r['inlet_water_temperature'] for r in ejector_res)), reverse=True)
        headers = ['t='] + temps
        data_1 = {r['inlet_water_temperature']: r['ejector_pressure_kPa'] for r in ejector_res if r['number_of_ejectors'] == 1}
        data_2 = {r['inlet_water_temperature']: r['ejector_pressure_kPa'] for r in ejector_res if r['number_of_ejectors'] == 2}
        row1 = ["**Включен 1**"] + [data_1.get(t, 0.0) for t in temps]
        row2 = ["**Включены**"] + [data_2.get(t, 0.0) for t in temps]
        ejector_table_str += create_markdown_table(headers, [row1, row2])

    return ejector_table_str

if __name__ == "__main__":
    final_report = run_simulation(wo=1200, wbc=0, b_label="1", r_raw_value=0.10, has_ejector_data=True)

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(final_report)

    print("Файл 'report.md' успешно создан")