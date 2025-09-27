import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from utils.calculation_engine import k_interpolation_data

def plot_extended_k_temp_graph():
    print("Создание интерполятора на основе исходных данных...")
    interpolator = RegularGridInterpolator(
        (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
        np.array(k_interpolation_data["k_values_matrix"]),
        method="linear",
        bounds_error=False,
        fill_value=None
    )

    new_speeds = np.arange(0, 10.1, 0.5)
    new_temperatures = np.array([0, 5, 15, 27, 38, 50, 70, 95, 120, 150, 175, 200])

    print("Расчет K_temp для расширенного диапазона (экстраполяция)...")
    SPEED_MESH, TEMP_MESH = np.meshgrid(new_speeds, new_temperatures)
    points_to_calculate = np.vstack([SPEED_MESH.ravel(), TEMP_MESH.ravel()]).T
    calculated_k_values = interpolator(points_to_calculate)
    new_k_matrix = calculated_k_values.reshape(len(new_temperatures), len(new_speeds))

    print("Построение графика...")
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(15, 10))

    for i, temp in enumerate(new_temperatures):
        k_values_for_temp = new_k_matrix[i, :]
        
        linestyle = '--' if temp in [0, 175, 200] else '-'
        linewidth = 1.5 if linestyle == '--' else 2.0
        
        current_marker = 'o' if linestyle == '-' else None

        ax.plot(
            new_speeds, 
            k_values_for_temp, 
            marker=current_marker,
            markersize=4,
            linestyle=linestyle,
            linewidth=linewidth,
            label=f'{temp} °C'
        )

    ax.set_title('Зависимость K_temp от скорости и температуры (с экстраполяцией)', fontsize=18, pad=20)
    ax.set_xlabel('Скорость воды, м/с', fontsize=14)
    ax.set_ylabel('Коэффициент теплопередачи, Вт/(м²·К)', fontsize=14)

    ax.set_xticks(np.arange(0, 10.1, 0.5))
    ax.set_xlim(0, 10)

    max_k = np.ceil(new_k_matrix.max() / 1000) * 1000
    ax.set_yticks(np.arange(0, max_k + 1000, 1000))
    ax.set_ylim(bottom=0)

    legend = ax.legend(title='Температура воды, °C', fontsize=11, loc='upper left')
    plt.setp(legend.get_title(), fontsize='12')

    ax.grid(True, which='both', linestyle='--', linewidth=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_extended_k_temp_graph()