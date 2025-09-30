/**
 * API клиент для взаимодействия с Condenser Calculation Service
 */

class CondenserAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    /**
     * Создание новой задачи расчёта
     * @param {Object} taskData - данные задачи (condenser_input.json)
     * @returns {Promise<Object>} - { task_id, status }
     */
    async createTask(taskData) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/tasks/condenser`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating task:', error);
            throw error;
        }
    }

    /**
     * Получение статуса задачи
     * @param {string} taskId - ID задачи
     * @returns {Promise<Object>} - статус задачи
     */
    async getTaskStatus(taskId) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/tasks/${taskId}/status`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting task status:', error);
            throw error;
        }
    }

    /**
     * Получение результатов расчёта
     * @param {string} taskId - ID задачи
     * @returns {Promise<Object>} - результаты расчёта
     */
    async getTaskResults(taskId) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/tasks/${taskId}/results`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting task results:', error);
            throw error;
        }
    }

    /**
     * Отмена задачи
     * @param {string} taskId - ID задачи
     * @returns {Promise<Object>}
     */
    async cancelTask(taskId) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/tasks/${taskId}/cancel`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error canceling task:', error);
            throw error;
        }
    }

    /**
     * Получение списка проектов
     * @returns {Promise<Array>}
     */
    async getProjects() {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/projects`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting projects:', error);
            throw error;
        }
    }

    /**
     * Получение истории коммитов для файла
     * @param {string} projectPath - путь к проекту
     * @param {string} filePath - путь к файлу
     * @returns {Promise<Array>}
     */
    async getFileHistory(projectPath, filePath) {
        try {
            const response = await fetch(
                `${this.baseURL}/api/v1/projects/${projectPath}/files/${encodeURIComponent(filePath)}/history`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting file history:', error);
            throw error;
        }
    }

    /**
     * Получение содержимого файла из определённого коммита
     * @param {string} projectPath - путь к проекту
     * @param {string} commitHash - хеш коммита
     * @param {string} filePath - путь к файлу
     * @returns {Promise<Object>}
     */
    async getFileContent(projectPath, commitHash, filePath) {
        try {
            const response = await fetch(
                `${this.baseURL}/api/v1/files/content?project_path=${projectPath}&commit_hash=${commitHash}&file_path=${encodeURIComponent(filePath)}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting file content:', error);
            throw error;
        }
    }
}

// Экспорт для использования в app.js
const api = new CondenserAPI();