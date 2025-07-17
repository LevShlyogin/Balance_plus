import numpy as np
from datetime import datetime

from utils.metrovickers_strategy import MetroVickersStrategy


def generate_md_report_file(strategy: MetroVickersStrategy, results: dict, params: dict, filename: str):
    report_lines = []

    report_lines.append(f"# Отчет по расчету тепловых характеристик")
    report_lines.append(f"**Дата и время генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Методика:** Метро-Виккерса (эмуляция `kondt2.xls`)")
    report_lines.append("\n---")

    report_lines.append("\n## 1. Исходные данные")

    report_lines.append("\n### 1.1. Геометрия и конструкция")
    report_lines.append("| Параметр                                       | Ключ в `params`                               | Значение | Ед. изм. |")
    report_lines.append("|:-----------------------------------------------|:----------------------------------------------|:--------:|:--------:|")
    report_lines.append(f"| Внутренний диаметр трубок                      | `diameter_inside_of_pipes`                    | `{params['diameter_inside_of_pipes']}`   | м        |")
    report_lines.append(f"| Толщина стенки трубок                          | `thickness_pipe_wall`                         | `{params['thickness_pipe_wall']}`     | м        |")
    report_lines.append(f"| Активная длина охлаждающих труб                | `length_cooling_tubes_of_the_main_bundle`     | `{params['length_cooling_tubes_of_the_main_bundle']}`      | м        |")
    report_lines.append(f"| Количество трубок (основной пучок)             | `number_cooling_tubes_of_the_main_bundle`     | `{params['number_cooling_tubes_of_the_main_bundle']}` | шт.      |")
    report_lines.append(f"| Количество трубок (встроенный пучок)           | `number_cooling_tubes_of_the_built-in_bundle` | `{params['number_cooling_tubes_of_the_built-in_bundle']}` | шт.      |")
    report_lines.append(f"| Количество трубок воздухоохладителя            | `number_air_cooler_total_pipes`               | `{params['number_air_cooler_total_pipes']}` | шт.      |")
    
    report_lines.append("\n### 1.2. Параметры режима")
    report_lines.append("| Параметр                                       | Ключ в `params`                               | Значение | Ед. изм.    |")
    report_lines.append("|:-----------------------------------------------|:----------------------------------------------|:--------:|:-----------:|")
    report_lines.append(f"| Число ходов охлаждающей воды                   | `number_cooling_water_passes_of_the_main_bundle`| `{params['number_cooling_water_passes_of_the_main_bundle']}`       | -        |")
    report_lines.append(f"| Вариант расчета (1-бойлер, 2-конденсатор)      | `VAR`                                         | `{params['VAR']}`       | -        |")
    report_lines.append(f"| Материал трубок                                | `material_name`                               | `{params['material_name']}` | -        |")
    report_lines.append(f"| Коэф-т теплопроводности материала              | `thermal_conductivity_cooling_surface_tube_material` | `{params['thermal_conductivity_cooling_surface_tube_material']}` | ккал/м*ч*°С |")

    report_lines.append("\n### 1.3. Параметры для итеративного расчета")
    report_lines.append(f"- **Расходы охлаждающей воды (м³/час):** `{params['mass_flow_cooling_water_variants']}`")
    report_lines.append(f"- **Средние температуры охлажд. воды (°С):** `{params['average_temp_variants']}`")
    report_lines.append(f"- **Коэффициенты загрязнения (β):** `{params['coefficient_b_variants']}`")

    report_lines.append("\n### 1.4. Стандартная таблица Метро-Виккерса (Коэффициент теплопередачи, ккал/м²*ч*°С)")
    temps = params['vik_table_temps']
    speeds = params['vik_table_speeds']
    k_values = params['vik_table_k_values']
    
    header_labels = ["Скорость, м/с"] + [f"{t}°C" for t in temps]
    report_lines.append("| " + " | ".join(header_labels) + " |")
    report_lines.append("|:---" + "|:---:" * len(header_labels))
    
    for i, speed in enumerate(speeds):
        row_values = [f"{speed:.1f}"] + [str(int(k)) for k in k_values[i]]
        report_lines.append("| " + " | ".join(row_values) + " |")

    report_lines.append("\n---")

    report_lines.append("\n## 2. Результаты расчета (Относительный недогрев)")

    sorted_beta_coeffs = sorted(results.keys(), reverse=True)

    for beta in sorted_beta_coeffs:
        report_lines.append(f"\n### Коэффициент загрязнения β = {beta:.2f}")
        
        res_header_labels = ["`tср`"] + [f"`{int(flow)}`" for flow in params['mass_flow_cooling_water_variants']]
        report_lines.append("| " + " | ".join(res_header_labels) + " |")
        report_lines.append("|:" + "---:|:" * len(res_header_labels))

        temp_data = results[beta]
        sorted_temps = sorted(temp_data.keys())

        for temp in sorted_temps:
            row_data = temp_data[temp]
            row_values = [f"{temp}°С"] + [f"{val:.4f}" if val is not None else "ERR" for val in row_data]
            report_lines.append("| " + " | ".join(row_values) + " |")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        print(f"\nОтчет успешно создан и сохранен в файл: {filename}")
    except IOError as e:
        print(f"\nОшибка при записи в файл {filename}: {e}")

def run_calculation_and_generate_report():
    params = {
        'diameter_inside_of_pipes': 0.02,
        'thickness_pipe_wall': 0.001,
        'length_cooling_tubes_of_the_main_bundle': 7.08,
        'number_cooling_tubes_of_the_main_bundle': 1754,
        'number_cooling_tubes_of_the_built-in_bundle': 0,
        'number_air_cooler_total_pipes': 418,
        'number_cooling_water_passes_of_the_main_bundle': 2,
        'VAR': 2, 
        'thermal_conductivity_cooling_surface_tube_material': 37,
        'material_name': "сплав МНЖ5-1",
        'vik_table_temps': np.array([5, 15, 27, 38, 50, 70, 95, 120, 150]),
        'vik_table_speeds': np.array([0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.7]),
        'vik_table_k_values': np.array([
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
            [3150, 3400, 3620, 3810, 3940, 4120, 4230, 4350, 4440], 
            [3250, 3500, 3710, 3910, 4040, 4220, 4350, 4440, 4540], 
            [3340, 3590, 3800, 3990, 4130, 4320, 4420, 4530, 4610], 
            [3440, 3690, 3870, 4050, 4180, 4390, 4500, 4600, 4670], 
            [3500, 3750, 3930, 4100, 4230, 4460, 4560, 4660, 4730], 
            [3560, 3810, 3990, 4160, 4290, 4520, 4620, 4720, 4790], 
            [3600, 3850, 4040, 4200, 4340, 4560, 4660, 4760, 4840], 
            [3630, 3880, 4060, 4230, 4360, 4590, 4690, 4790, 4850]
        ]),
        'mass_flow_cooling_water_variants': [1200, 1250, 1500, 1750, 2000, 2250, 2500],
        'average_temp_variants': [35, 37, 40],
        'coefficient_b_variants': [1.00, 0.75],
    }
    
    try:
        print("Подготовка к расчету...")
        strategy = MetroVickersStrategy(params)
        
        print("Выполнение расчетов...")
        all_results = {
            beta: {
                temp: [strategy.calculate_relative_underheating(flow, temp, beta) for flow in params['mass_flow_cooling_water_variants']]
                for temp in params['average_temp_variants']
            }
            for beta in params['coefficient_b_variants']
        }
        
        print("Генерация отчета...")
        report_filename = f"report_metrovickers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        generate_md_report_file(strategy, all_results, params, report_filename)

    except KeyError as e:
        print(f"\n**ОШИБКА:** В словаре 'params' отсутствует необходимый ключ: `{e}`")
    except Exception as e:
        print(f"\n**Произошла непредвиденная ошибка:**\n```\n{e}\n```")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_calculation_and_generate_report()