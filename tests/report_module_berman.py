from utils.module_berman import calculate_thermal_characteristics
from datetime import datetime

def generate_markdown_report(params, results, filename="report.md"):
    def group_results(main_results):
        grouped = {}
        for row in main_results:
            key = (row['W1'], row['W2'], row['R_input'], row['Beta'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(row)
        return grouped

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Отчет по тепловому расчету конденсатора\n\n")
        f.write(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## 1. Исходные данные\n\n")
        f.write("| Параметр | Значение | Ед. изм. |\n")
        f.write("|:---|:---:|:---|\n")
        f.write(f"| Активная длина трубок (осн. / встр. пучок) | {params['A'][1]} / {params['A'][2]} | м |\n")
        f.write(f"| Число ходов воды (осн. / встр. пучок) | {params['Z'][1]} / {params['Z'][2]} | - |\n")
        f.write(f"| Кол-во трубок (осн. / встр. пучок) | {params['FN'][1]} / {params['FN'][2]} | шт. |\n")
        f.write(f"| Теплоемкость пара (DI) | {params['DI']} | ккал/кг·°C |\n")
        f.write(f"| Номинальный расход пара (DK) | {params['DK']} | т/ч |\n")
        f.write(f"| Теплопроводность материала труб (DLCT) | {params['DLCT']} | Вт/м·К |\n")
        f.write(f"| Номер варианта (BAP) | {params['BAP']} | - |\n")
        f.write(f"| Внутренний диаметр трубок (DD) | {params['DD'] * 1000} | мм |\n")
        f.write(f"| Толщина стенки трубок (DCT) | {params['DCT'] * 1000} | мм |\n")
        f.write(f"| Присос воздуха для эжектора (GV) | {params['GV']} | кг/ч |\n\n")

        f.write("## 2. Результаты расчетов\n\n")
        
        grouped_data = group_results(results['main_results'])
        
        for key, rows in grouped_data.items():
            w1, w2, r_input, beta = key
            f.write(f"### Режим: W1={w1} м³/ч, W2={w2} м³/ч, R={r_input} (β={beta})\n\n")
            
            f.write("| D, т/ч | t1(1),°C | t1(2),°C | T3(1) | T3(2) | T4(1) | T4(2) | **TK, °C** | **PS, кПа** |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            
            # Строки таблицы
            for row in rows:
                f.write(
                    f"| {row['D']:.1f} "
                    f"| {row['T1_1']:.1f} "
                    f"| {row['T1_2']:.1f} "
                    f"| {row['T3_1']:.3f} "
                    f"| {row['T3_2']:.3f} "
                    f"| {row['T4_1']:.3f} "
                    f"| {row['T4_2']:.3f} "
                    f"| **{row['TK']:.3f}** "
                    f"| **{row['PS']:.5f}** |\n"
                )
            f.write("\n")

        if results['ejector_results']['temps']:
            f.write("## 3. Тепловые характеристики с учетом эжектора\n\n")
            
            ej_res = results['ejector_results']
            temps_header = " | ".join([f"{t:.1f}°C" for t in ej_res['temps']])
            
            f.write(f"| Характеристика | {temps_header} |\n")
            f.write(f"|:---|{'|:'.join(['---:'] * len(ej_res['temps']))}|\n")
            
            pk1_vals = " | ".join([f"{pk:.3f}" for pk in ej_res['pk_values_1']])
            pk2_vals = " | ".join([f"{pk:.3f}" for pk in ej_res['pk_values_2']])
            
            f.write(f"| Давление с 1 эжектором, кПа | {pk1_vals} |\n")
            f.write(f"| Давление с 2 эжекторами, кПа | {pk2_vals} |\n")
    
    print(f"Отчет успешно сгенерирован в файле: {filename}")


if __name__ == "__main__":
    input_params = {
        'A': {1: 1.0, 2: 1.0},
        'Z': {1: 2, 2: 2},
        'FN': {1: 10000, 2: 3000},
        'DI': 520.0,
        'DK': 540.0,
        'DLCT': 37.0,
        'BAP': 3,
        'DD': 22.0 / 1000.0,
        'DCT': 1.0 / 1000.0,
        'W': [
            [14215.0],
            [3285.0]
        ],
        'T1': [
            [27.5, 32.0],
            [27.5, 32.0]
        ],
        'D': [30.0, 80.0, 130.0, 180.0, 230.0],
        'R': [0.10, 104.40],
        'RBETA': [1.00, 0.75],
        'GV': 20.0
    }

    calculation_results = calculate_thermal_characteristics(input_params)

    generate_markdown_report(input_params, calculation_results, filename="module_berman_report.md")