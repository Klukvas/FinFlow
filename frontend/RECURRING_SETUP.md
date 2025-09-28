# Настройка повторяющихся платежей

## Переменные окружения

Создайте файл `.env` в корне проекта frontend со следующим содержимым:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8001
VITE_CATEGORY_SERVICE_URL=http://localhost:8002
VITE_EXPENSE_SERVICE_URL=http://localhost:8003
VITE_INCOME_SERVICE_URL=http://localhost:8004
VITE_RECURRING_SERVICE_URL=http://localhost:8005

# App Configuration
VITE_APP_NAME=Financial Accounting
VITE_APP_VERSION=1.0.0
VITE_DEBUG=true
```

## Запуск

1. Установите зависимости:
```bash
npm install
```

2. Запустите сервисы:
```bash
docker-compose up recurring_service
```

3. Запустите фронтенд:
```bash
npm run dev
```

## Функциональность

### Повторяющиеся платежи
- Создание, редактирование и удаление повторяющихся платежей
- Поддержка различных типов расписания (ежедневно, еженедельно, ежемесячно, ежегодно)
- Управление статусами (активен, приостановлен, завершен, отменен)
- Статистика выполнения платежей
- Фильтрация и поиск

### Типы расписания
- **Ежедневно**: каждый день
- **Еженедельно**: выбранный день недели
- **Ежемесячно**: выбранное число месяца
- **Ежегодно**: выбранная дата (месяц и день)

### API интеграция
- Полная интеграция с recurring_service
- Автоматическое создание расходов и доходов
- Валидация категорий через category_service
