[![Версия](https://img.shields.io/badge/version-0.1.0--alpha-blue)](https://github.com/your-org/balance-plus/releases)
[![Статус сборки](https://img.shields.io/gitlab/pipeline-status/your-group/your-project?branch=main)](https://gitlab.com/your-group/your-project/-/pipelines)
[![Лицензия](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.70+-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen?logo=vuedotjs&logoColor=white)](https://vuejs.org/)

**Balance_plus** – это веб-приложение, предназначенное для автоматизации и оптимизации рабочих процессов инженеров-конструкторов и их руководителей в отделе расчетов. Система интегрируется с GitLab для управления проектами, задачами и версионированием расчетных данных, а также оркестрирует запуск инженерных расчетов на специализированных микросервисах.

---

## 🌟 Ключевые возможности

*   **🚀 Централизованное управление проектами:** Создание и ведение расчетных проектов с использованием шаблонов GitLab.
*   **📝 Управление задачами:** Интеграция с GitLab Issues для постановки, отслеживания и выполнения расчетных задач.
*   **💾 Версионирование данных:** Хранение и управление JSON-файлами с геометрическими, термодинамическими параметрами и результатами расчетов в Git.
*   **✏️ Удобное редактирование параметров:** "Человекочитаемый" интерфейс для ввода и модификации сложных JSON-структур.
*   **🔄 Копирование геометрии:** Инструмент для переноса частей геометрии между проектами.
*   **⚙️ Оркестрация расчетов:** Запуск и мониторинг инженерных расчетов, выполняемых внешними специализированными микросервисами.
*   **📊 Визуализация результатов:** Отображение результатов расчетов в понятном табличном виде.
*   **🔒 Безопасность и права доступа:** Аутентификация через GitLab и ролевая модель доступа.

---

## 🛠️ Технологический стек

### Backend
*   **Язык:** Python 3.9+
*   **Фреймворк:** FastAPI
*   **Асинхронные задачи:** Celery
*   **Брокер сообщений / Кэш:** Redis
*   **База данных (в перспективе):** PostgreSQL
*   **ORM (в перспективе):** SQLAlchemy
*   **Взаимодействие с GitLab:** `python-gitlab`, `httpx`
*   **Работа с JSON:** Встроенный `json`, `Pydantic`, `simpleeval`
*   **Свойства воды/пара:** `CoolProp` / `iapws`
*   **Работа с XML:** `lxml`

### Frontend
*   **Фреймворк:** Vue.js 3 (предпочтительно) или React
*   **UI-библиотека:** Quasar Framework / Vuetify (для Vue) или Material-UI / Ant Design (для React)
*   **HTTP-клиент:** Axios
*   **Управление состоянием:** Pinia / Vuex (для Vue) или Redux / MobX (для React)

### Инфраструктура и DevOps
*   **Контейнеризация:** Docker, Docker Compose
*   **CI/CD:** GitLab CI/CD
*   **Веб-сервер (для FastAPI):** Uvicorn
*   **ОС для развертывания:** Linux

---

## 🚀 Начало работы

### Предварительные требования

*   Docker и Docker Compose установлены.
*   Доступ к self-hosted инстансу GitLab с правами на создание проектов, групп и API-токенов.
*   Настроенные внешние расчетные микросервисы (согласно документации).
*   Python 3.9+ и Node.js (с npm/yarn) для локальной разработки без Docker (опционально).

### Установка и запуск (с использованием Docker Compose)

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://gitlab.com/your-group/your-project.git
    cd balance-plus
    ```

2.  **Конфигурация:**
    *   Скопируйте `.env.example` в `.env` в корневой директории и в директории `backend/`.
        ```bash
        cp .env.example .env
        cp backend/.env.example backend/.env
        ```
    *   Отредактируйте файлы `.env`, указав необходимые параметры:
        *   `GITLAB_URL`: URL вашего GitLab инстанса.
        *   `GITLAB_APP_ID`, `GITLAB_APP_SECRET`: для OAuth2 аутентификации.
        *   `GITLAB_PERSONAL_ACCESS_TOKEN`: сервисный токен с правами `api, read_repository, write_repository` (для операций от имени приложения).
        *   Адреса внешних расчетных микросервисов.
        *   Другие специфичные для проекта настройки.

3.  **Сборка и запуск контейнеров:**
    ```bash
    docker-compose up --build -d
    ```
    Это запустит backend, frontend (в режиме разработки или production, в зависимости от конфигурации Dockerfile), Redis и (если настроено) PostgreSQL.

4.  **Доступ к приложению:**
    Откройте в браузере `http://localhost:<FRONTEND_PORT>` (порт обычно 8080 или 3000, см. `docker-compose.yml`).

### Локальная разработка (без Docker, для отдельных компонентов)

Инструкции для локального запуска каждого компонента (backend, frontend) будут размещены в их соответствующих директориях (`backend/README.md`, `frontend/README.md`).

---

## 📝 Пользовательские сценарии (Основные)

### Для Руководителя:
1.  **Создание проекта:**
    *   Авторизуется в Balance_plus.
    *   Создаёт репозиторий проекта в GitLab из шаблона, с автоматическим созданием базовых JSON-файлов.
    *   (Опционально) Заменяет JSON-файлы данными из проекта-аналога.
    *   Создаёт "Project" (доску задач) в GitLab из шаблона, с автоматическим добавлением labels, milestones и участников.
2.  **Постановка задачи:**
    *   Создаёт задачу для инженера-расчётчика, назначает исполнителя, проставляет атрибуты.
    *   Автоматически создаётся ветка в Git для этой задачи.
3.  **Контроль и приемка:**
    *   Отслеживает статус задач.
    *   Просматривает результаты расчетов в Balance_plus.
    *   Работает с Merge Request в GitLab для приемки или возврата задачи.

### Для Инженера-расчётчика:
1.  **Работа с задачами:**
    *   Авторизуется в Balance_plus.
    *   Видит список назначенных ему задач.
    *   Выбирает задачу, при этом автоматически подгружаются нужные JSON-файлы из соответствующей ветки.
2.  **Редактирование параметров:**
    *   Вносит изменения в геометрию и термодинамические параметры через специализированные интерфейсы.
    *   Использует инструмент копирования частей геометрии.
    *   Сохраняет изменения (коммитит JSON-файлы в свою ветку).
    *   Выбирает режимы для расчета.
3.  **Расчет и результаты:**
    *   Нажимает кнопку "Расчёт".
    *   Смотрит результаты расчётов в табличном виде.
    *   Сохраняет результаты (коммитит JSON-файл с результатами).
4.  **Сдача задачи:**
    *   Отправляет задачу на проверку руководителю (создает Merge Request в GitLab).

---

## 🏗️ Архитектура

Краткое описание архитектуры:
*   **Frontend (SPA):** Пользовательский интерфейс.
*   **Backend (FastAPI):** Обработка запросов, бизнес-логика, интеграция с GitLab, оркестрация расчетов.
*   **Celery Workers:** Выполнение асинхронных/длительных задач.
*   **Redis:** Брокер сообщений для Celery, кэширование.
*   **GitLab:** Хранение данных (JSON в Git), управление задачами, CI/CD, аутентификация.
*   **Внешние расчетные микросервисы:** Выполнение специализированных инженерных расчетов.

*Для более детального представления см. [ДИАГРАММА АРХИТЕКТУРЫ](docs/architecture.md) (предполагается, что диаграммы будут вынесены в отдельный файл или раздел).*

---

## 📂 Структура репозитория

```
.
├── backend/                  # Исходный код Backend (FastAPI)
│   ├── app/                  # Основной код приложения
│   ├── tests/                # Тесты для Backend
│   ├── alembic/              # Миграции БД (если используется Alembic)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Исходный код Frontend (Vue.js/React)
│   ├── src/                  # Основной код приложения
│   ├── public/
│   ├── tests/                # Тесты для Frontend
│   ├── Dockerfile
│   └── .env.example
├── docs/                     # Документация проекта (ТЗ, диаграммы, и т.д.)
│   ├── architecture.md
│   └── data_flow_diagrams.md
├── .gitlab-ci.yml            # Конфигурация GitLab CI/CD
├── docker-compose.yml        # Docker Compose конфигурация для запуска всех сервисов
├── .env.example              # Пример переменных окружения для docker-compose
├── README.md                 # Этот файл
├── LICENSE                   # Информация о лицензии
└── .gitignore
```

---

## 🤝 Участие в разработке (Contributing)

Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для получения информации о том, как внести свой вклад в проект, включая правила оформления кода, процесс создания Merge Requests и т.д.

Основные шаги:
1.  Создайте Issue с описанием проблемы или предложения.
2.  Форкните репозиторий или создайте ветку от `develop` (или `main`, в зависимости от Git flow).
3.  Внесите изменения и напишите тесты.
4.  Убедитесь, что все тесты проходят и линтеры не выдают ошибок.
5.  Создайте Merge Request в основную ветку разработки.

---

## 🐛 Сообщить об ошибке (Reporting Bugs)

Если вы обнаружили ошибку, пожалуйста, создайте Issue в GitLab, предоставив как можно больше информации:
*   Шаги для воспроизведения.
*   Ожидаемое поведение.
*   Фактическое поведение.
*   Версия приложения, браузера, ОС.
*   Скриншоты (если применимо).
*   Логи ошибок (если доступны).

---

## 📜 Лицензия

Данный проект распространяется под [УКАЗАТЬ ТИП ЛИЦЕНЗИИ - например, Proprietary, MIT, Apache 2.0](LICENSE).
(Если Proprietary, то файл LICENSE может содержать просто "All Rights Reserved" или ссылку на внутренние документы).

---

## 📞 Контакты

*   **Руководитель проекта / Product Owner:** [Ваше Имя/Email/GitLab Username]
*   **Технический лидер / Основной разработчик:** [Имя/Email/GitLab Username]

---
