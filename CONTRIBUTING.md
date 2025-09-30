# Contributing to Condenser Calculation Service

Спасибо за интерес к проекту! Мы приветствуем любой вклад.

## 🚀 Процесс разработки

### 1. Форк и клонирование

```bash
git clone https://gitlab.example.com/balanceplus/condenser-service.git
cd condenser-service
```

### 2. Создание ветки

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/your-bug-fix
```

### 3. Установка зависимостей

```bash
poetry install
```

### 4. Внесение изменений

- Следуйте стандартам PEP 8
- Добавляйте docstrings ко всем функциям
- Пишите тесты для нового функционала

### 5. Запуск тестов

```bash
make test-cov
```

### 6. Форматирование кода

```bash
make format
make lint
```

### 7. Коммит изменений

Следуйте [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new calculation strategy"
git commit -m "fix: resolve geometry path issue"
git commit -m "docs: update README"
```

### 8. Push и создание Merge Request

```bash
git push origin feature/your-feature-name
```

Создайте Merge Request в GitLab с описанием изменений.

---

## 📋 Стандарты кода

### Python

- **PEP 8** для стиля кода
- **Black** для автоформатирования (line-length=120)
- **isort** для сортировки импортов
- **Type hints** везде, где возможно
- **Docstrings** для всех публичных функций

### Тестирование

- Минимум **80% coverage**
- Unit-тесты для всех новых функций
- Integration-тесты для Celery задач

### Документация

- Обновляйте README при добавлении новых функций
- Добавляйте примеры использования
- Документируйте все параметры конфигурации

---

## 🐛 Reporting Bugs

Создайте issue в GitLab со следующей информацией:

- Описание проблемы
- Шаги для воспроизведения
- Ожидаемое поведение
- Актуальное поведение
- Версия сервиса
- Логи (если применимо)

---

## 💡 Feature Requests

Создайте issue с меткой `enhancement` и опишите:

- Проблему, которую решает новая функция
- Предлагаемое решение
- Альтернативные варианты

---

## 📞 Контакты

- **Email**: dev-team@balanceplus.example
- **Slack**: #condenser-service
- **Wiki**: https://wiki.balanceplus.example
