/**
 * Frontend application logic for Condenser Calculation Service
 */

let currentTaskId = null;
let statusCheckInterval = null;
let resultsData = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    loadExample();
});

/**
 * Инициализация формы и обработчиков событий
 */
function initializeForm() {
    const form = document.getElementById('calculationForm');
    const strategySelect = document.getElementById('strategy');

    // Обработчик смены стратегии
    strategySelect.addEventListener('change', (e) => {
        showStrategyParams(e.target.value);
    });

    // Обработчик отправки формы
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitCalculation();
    });

    // Показываем параметры для стратегии по умолчанию
    showStrategyParams(strategySelect.value);
}

/**
 * Показать параметры для выбранной стратегии
 */
function showStrategyParams(strategy) {
    const allParams = document.querySelectorAll('.strategy-params');
    allParams.forEach(params => params.style.display = 'none');

    const currentParams = document.getElementById(`${strategy}Params`);
    if (currentParams) {
        currentParams.style.display = 'block';
    }
}

/**
 * Загрузка примера данных
 */
function loadExample() {
    // Данные уже заполнены в HTML по умолчанию
    addLog('Загружен пример данных для расчёта', 'info');
}

/**
 * Отправка задачи на расчёт
 */
async function submitCalculation() {
    try {
        addLog('Подготовка данных для отправки...', 'info');

        const inputData = buildInputJSON();
        
        addLog('Валидация данных...', 'info');
        validateInputData(inputData);

        addLog('Отправка задачи на сервер...', 'info');

        // Имитация создания задачи (т.к. у нас нет реального API)
        // В реальном приложении здесь будет: const response = await api.createTask(inputData);
        const mockTaskId = generateTaskId();
        
        addLog(`Задача создана: ${mockTaskId}`, 'success');
        
        currentTaskId = mockTaskId;
        showTaskStatus(mockTaskId);
        
        // Запуск имитации выполнения задачи
        simulateTaskExecution(mockTaskId);

    } catch (error) {
        addLog(`Ошибка: ${error.message}`, 'error');
        alert(`Ошибка при создании задачи: ${error.message}`);
    }
}

/**
 * Построение JSON для condenser_input.json
 */
function buildInputJSON() {
    const strategy = document.getElementById('strategy').value;
    
    const inputData = {
        schema_version: "1.2",
        _meta: {
            target_project_path: document.getElementById('targetProject').value
        },
        geometry_source: {
            type: "reference",
            source_info: {
                project_path: document.getElementById('geomProjectPath').value,
                commit_hash: document.getElementById('geomCommitHash').value
            },
            path: document.getElementById('geomPath').value
        },
        parameters_source: {
            type: "reference",
            source_info: {
                project_path: document.getElementById('paramsProjectPath').value,
                commit_hash: document.getElementById('paramsCommitHash').value
            },
            path: document.getElementById('paramsPath').value || null
        },
        calculation_strategy: strategy,
        parameters: buildParametersForStrategy(strategy)
    };

    return inputData;
}

/**
 * Построение параметров в зависимости от стратегии
 */
function buildParametersForStrategy(strategy) {
    switch(strategy) {
        case 'berman':
            return {
                mass_flow_steam_list: parseNumberArray(document.getElementById('bermanSteamFlow').value),
                enthalpy_flow_path_1: parseFloat(document.getElementById('bermanEnthalpy').value),
                mass_flow_cooling_water_list: parseNumberArray(document.getElementById('bermanWaterFlow').value),
                temperature_cooling_water_1_list: parseNumberArray(document.getElementById('bermanWaterTemp').value),
                coefficient_R_list: parseNumberArray(document.getElementById('bermanCoeffR').value),
                mass_flow_air: parseFloat(document.getElementById('bermanAirFlow').value) || 0,
                BAP: 1
            };
        
        case 'metro_vickers':
            return {
                mass_flow_cooling_water: parseFloat(document.getElementById('mvWaterFlow').value),
                temperature_cooling_water_1: parseFloat(document.getElementById('mvWaterTemp').value),
                coefficient_b: parseFloat(document.getElementById('mvCoeffB').value),
                mass_flow_flow_path_1: parseFloat(document.getElementById('mvSteamFlow').value),
                degree_dryness_flow_path_1: parseFloat(document.getElementById('mvDryness').value)
            };
        
        case 'vku':
            return {
                mass_flow_flow_path_1: parseFloat(document.getElementById('vkuSteamFlow').value),
                degree_dryness_flow_path_1: parseFloat(document.getElementById('vkuDryness').value),
                temperature_air: parseFloat(document.getElementById('vkuAirTemp').value) || 20.0,
                mass_flow_steam_nom: parseFloat(document.getElementById('vkuNomSteamFlow').value),
                degree_dryness_steam_nom: parseFloat(document.getElementById('vkuNomDryness').value)
            };
        
        default:
            return {};
    }
}

/**
 * Парсинг массива чисел из строки
 */
function parseNumberArray(str) {
    return str.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
}

/**
 * Валидация входных данных
 */
function validateInputData(data) {
    if (!data.geometry_source.source_info.commit_hash) {
        throw new Error('Geometry source commit_hash is required');
    }
    
    if (!data.parameters_source.source_info.commit_hash) {
        throw new Error('Parameters source commit_hash is required');
    }
    
    if (Object.keys(data.parameters).length === 0) {
        throw new Error('Parameters cannot be empty');
    }
}

/**
 * Показать статус задачи
 */
function showTaskStatus(taskId) {
    document.getElementById('statusCard').style.display = 'block';
    document.getElementById('taskId').textContent = taskId;
    document.getElementById('taskState').textContent = 'PENDING';
    document.getElementById('taskState').className = 'badge pending';
    document.getElementById('progressBar').style.width = '0%';
}

/**
 * Имитация выполнения задачи (для демонстрации UI)
 */
function simulateTaskExecution(taskId) {
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += 10;
        
        if (progress <= 30) {
            updateTaskStatus('PENDING', progress);
            addLog(`Задача в очереди... (${progress}%)`, 'info');
        } else if (progress <= 90) {
            updateTaskStatus('RUNNING', progress);
            addLog(`Выполнение расчёта... (${progress}%)`, 'info');
        } else {
            clearInterval(interval);
            updateTaskStatus('SUCCESS', 100);
            addLog('Расчёт завершён успешно!', 'success');
            showResults(generateMockResults());
        }
    }, 800);
}

/**
 * Обновление статуса задачи в UI
 */
function updateTaskStatus(status, progress) {
    const stateElement = document.getElementById('taskState');
    stateElement.textContent = status;
    stateElement.className = `badge ${status.toLowerCase()}`;
    
    document.getElementById('progressBar').style.width = `${progress}%`;
}

/**
 * Генерация mock результатов для демонстрации
 */
function generateMockResults() {
    const strategy = document.getElementById('strategy').value;
    
    const baseResults = {
        schema_version: "1.2",
        input_commit_hash: document.getElementById('commitHash').value,
        calculation_strategy: strategy,
        _meta: {
            target_project: {
                path: document.getElementById('targetProject').value,
                attributes: {}
            },
            sources: {
                geometry: {
                    project_path: document.getElementById('geomProjectPath').value,
                    commit_hash: document.getElementById('geomCommitHash').value,
                    path: document.getElementById('geomPath').value
                },
                parameters: {
                    project_path: document.getElementById('paramsProjectPath').value,
                    commit_hash: document.getElementById('paramsCommitHash').value,
                    path: document.getElementById('paramsPath').value
                }
            }
        },
        results: {}
    };

    // Генерация результатов в зависимости от стратегии
    switch(strategy) {
        case 'berman':
            baseResults.results.berman_results = {
                main_results: [
                    {
                        condenser_pressure_Pa: 4521.3,
                        saturation_temperature_C: 30.8,
                        undercooling_main_bundle_C: 2.1,
                        undercooling_built_in_bundle_C: 0.0
                    },
                    {
                        condenser_pressure_Pa: 4832.7,
                        saturation_temperature_C: 31.5,
                        undercooling_main_bundle_C: 2.3,
                        undercooling_built_in_bundle_C: 0.0
                    }
                ],
                ejector_results: []
            };
            break;
        
        case 'metro_vickers':
            baseResults.results.metro_vickers_results = {
                pressure_flow_path_1: 0.0461,
                temperature_saturation_steam: 30.85,
                speed_cooling_water: 1.87,
                coefficient_K: 3842.5,
                coefficient_R: 0.00012,
                temperature_cooling_water_2: 23.8
            };
            break;
        
        case 'vku':
            baseResults.results.vku_results = {
                pressure_flow_path_1: 0.0875,
                mass_flow_reduced_steam_condencer: 89.47
            };
            break;
    }

    return baseResults;
}

/**
 * Отображение результатов
 */
function showResults(results) {
    resultsData = results;
    
    document.getElementById('resultsCard').style.display = 'block';
    document.getElementById('resultsJson').textContent = JSON.stringify(results, null, 2);
    
    // Прокрутка к результатам
    document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Проверка статуса задачи (для реального API)
 */
async function checkStatus() {
    if (!currentTaskId) {
        alert('Нет активной задачи');
        return;
    }

    try {
        addLog(`Проверка статуса задачи ${currentTaskId}...`, 'info');
        
        // В реальном приложении:
        // const status = await api.getTaskStatus(currentTaskId);
        // updateTaskStatus(status.state, status.progress);
        
        addLog('Статус обновлён', 'success');
    } catch (error) {
        addLog(`Ошибка при проверке статуса: ${error.message}`, 'error');
    }
}

/**
 * Скачивание результатов в JSON
 */
function downloadResults() {
    if (!resultsData) {
        alert('Нет результатов для скачивания');
        return;
    }

    const dataStr = JSON.stringify(resultsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `condenser_results_${currentTaskId}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    addLog('Результаты скачаны', 'success');
}

/**
 * Сброс формы и начало нового расчёта
 */
function resetForm() {
    currentTaskId = null;
    resultsData = null;
    
    document.getElementById('statusCard').style.display = 'none';
    document.getElementById('resultsCard').style.display = 'none';
    
    clearLogs();
    addLog('Готов к новому расчёту', 'info');
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Добавление записи в лог
 */
function addLog(message, type = 'info') {
    const logsContainer = document.getElementById('logs');
    const timestamp = new Date().toLocaleTimeString('ru-RU');
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type} new`;
    logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span>${message}`;
    
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
    
    // Убираем класс 'new' после анимации
    setTimeout(() => logEntry.classList.remove('new'), 1000);
}

/**
 * Очистка логов
 */
function clearLogs() {
    const logsContainer = document.getElementById('logs');
    logsContainer.innerHTML = '<div class="log-entry info">Логи очищены</div>';
}

/**
 * Генерация случайного ID задачи
 */
function generateTaskId() {
    return 'task-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Экспорт конфигурации в JSON
 */
function exportConfiguration() {
    const config = buildInputJSON();
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'condenser_input.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    addLog('Конфигурация экспортирована', 'success');
}

/**
 * Импорт конфигурации из JSON
 */
function importConfiguration(file) {
    const reader = new FileReader();
    
    reader.onload = (e) => {
        try {
            const config = JSON.parse(e.target.result);
            loadConfigurationToForm(config);
            addLog('Конфигурация импортирована', 'success');
        } catch (error) {
            addLog(`Ошибка импорта: ${error.message}`, 'error');
            alert('Ошибка при чтении файла конфигурации');
        }
    };
    
    reader.readAsText(file);
}

/**
 * Загрузка конфигурации в форму
 */
function loadConfigurationToForm(config) {
    document.getElementById('targetProject').value = config._meta.target_project_path;
    document.getElementById('geomProjectPath').value = config.geometry_source.source_info.project_path;
    document.getElementById('geomCommitHash').value = config.geometry_source.source_info.commit_hash;
    document.getElementById('geomPath').value = config.geometry_source.path;
    
    document.getElementById('paramsProjectPath').value = config.parameters_source.source_info.project_path;
    document.getElementById('paramsCommitHash').value = config.parameters_source.source_info.commit_hash;
    if (config.parameters_source.path) {
        document.getElementById('paramsPath').value = config.parameters_source.path;
    }
    
    document.getElementById('strategy').value = config.calculation_strategy;
    showStrategyParams(config.calculation_strategy);
    
    // Загрузка параметров стратегии
    loadStrategyParameters(config.calculation_strategy, config.parameters);
}

/**
 * Загрузка параметров стратегии из конфигурации
 */
function loadStrategyParameters(strategy, params) {
    switch(strategy) {
        case 'berman':
            if (params.mass_flow_steam_list) {
                document.getElementById('bermanSteamFlow').value = params.mass_flow_steam_list.join(', ');
            }
            if (params.enthalpy_flow_path_1) {
                document.getElementById('bermanEnthalpy').value = params.enthalpy_flow_path_1;
            }
            if (params.mass_flow_cooling_water_list) {
                document.getElementById('bermanWaterFlow').value = params.mass_flow_cooling_water_list.join(', ');
            }
            if (params.temperature_cooling_water_1_list) {
                document.getElementById('bermanWaterTemp').value = params.temperature_cooling_water_1_list.join(', ');
            }
            if (params.coefficient_R_list) {
                document.getElementById('bermanCoeffR').value = params.coefficient_R_list.join(', ');
            }
            if (params.mass_flow_air !== undefined) {
                document.getElementById('bermanAirFlow').value = params.mass_flow_air;
            }
            break;
        
        case 'metro_vickers':
            if (params.mass_flow_cooling_water) {
                document.getElementById('mvWaterFlow').value = params.mass_flow_cooling_water;
            }
            if (params.temperature_cooling_water_1) {
                document.getElementById('mvWaterTemp').value = params.temperature_cooling_water_1;
            }
            if (params.coefficient_b) {
                document.getElementById('mvCoeffB').value = params.coefficient_b;
            }
            if (params.mass_flow_flow_path_1) {
                document.getElementById('mvSteamFlow').value = params.mass_flow_flow_path_1;
            }
            if (params.degree_dryness_flow_path_1) {
                document.getElementById('mvDryness').value = params.degree_dryness_flow_path_1;
            }
            break;
        
        case 'vku':
            if (params.mass_flow_flow_path_1) {
                document.getElementById('vkuSteamFlow').value = params.mass_flow_flow_path_1;
            }
            if (params.degree_dryness_flow_path_1) {
                document.getElementById('vkuDryness').value = params.degree_dryness_flow_path_1;
            }
            if (params.temperature_air) {
                document.getElementById('vkuAirTemp').value = params.temperature_air;
            }
            if (params.mass_flow_steam_nom) {
                document.getElementById('vkuNomSteamFlow').value = params.mass_flow_steam_nom;
            }
            if (params.degree_dryness_steam_nom) {
                document.getElementById('vkuNomDryness').value = params.degree_dryness_steam_nom;
            }
            break;
    }
}