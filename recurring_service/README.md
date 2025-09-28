# Recurring Payments Service

Сервис для управления повторяющимися платежами в системе учета финансов.

## Возможности

- Создание, редактирование и удаление повторяющихся платежей
- Поддержка различных типов расписания (ежедневно, еженедельно, ежемесячно, ежегодно)
- Автоматическое выполнение платежей по расписанию
- Интеграция с сервисами расходов, доходов и категорий
- Управление статусами платежей (активен, приостановлен, завершен, отменен)
- Отслеживание истории выполнения платежей

## Архитектура

### Модели данных

**RecurringPayment** - основная модель повторяющегося платежа:
- `id` - уникальный идентификатор
- `user_id` - ID пользователя
- `name` - название платежа
- `description` - описание
- `amount` - сумма
- `currency` - валюта
- `category_id` - ID категории
- `payment_type` - тип платежа (expense/income)
- `schedule_type` - тип расписания (daily/weekly/monthly/yearly)
- `schedule_config` - конфигурация расписания
- `start_date` - дата начала
- `end_date` - дата окончания (опционально)
- `status` - статус (active/paused/completed/cancelled)
- `last_executed` - дата последнего выполнения
- `next_execution` - дата следующего выполнения

**PaymentSchedule** - расписание выполнения платежей:
- `id` - уникальный идентификатор
- `recurring_payment_id` - ID повторяющегося платежа
- `execution_date` - дата выполнения
- `status` - статус (pending/executed/failed)
- `created_expense_id` - ID созданного расхода
- `created_income_id` - ID созданного дохода
- `error_message` - сообщение об ошибке

### Типы расписания

1. **daily** - каждый день
   - `schedule_config`: `{}`

2. **weekly** - еженедельно
   - `schedule_config`: `{"day_of_week": 0-6}` (0=воскресенье)

3. **monthly** - ежемесячно
   - `schedule_config`: `{"day_of_month": 1-31}`

4. **yearly** - ежегодно
   - `schedule_config`: `{"month": 1-12, "day": 1-31}`

## API Endpoints

### Публичные API

#### Создание повторяющегося платежа
```
POST /api/v1/recurring-payments/?user_id={user_id}
```

#### Получение списка платежей
```
GET /api/v1/recurring-payments/?user_id={user_id}&status={status}&payment_type={type}&page={page}&size={size}
```

#### Получение платежа по ID
```
GET /api/v1/recurring-payments/{payment_id}?user_id={user_id}
```

#### Обновление платежа
```
PUT /api/v1/recurring-payments/{payment_id}?user_id={user_id}
```

#### Удаление платежа
```
DELETE /api/v1/recurring-payments/{payment_id}?user_id={user_id}
```

#### Приостановка платежа
```
POST /api/v1/recurring-payments/{payment_id}/pause?user_id={user_id}
```

#### Возобновление платежа
```
POST /api/v1/recurring-payments/{payment_id}/resume?user_id={user_id}
```

#### Получение расписания платежа
```
GET /api/v1/recurring-payments/{payment_id}/schedules?user_id={user_id}&status={status}&execution_date_from={date}&execution_date_to={date}&page={page}&size={size}
```

#### Статистика платежей
```
GET /api/v1/recurring-payments/statistics/summary?user_id={user_id}
```

### Внутренние API (для cron)

#### Выполнение платежей
```
POST /internal/execute-recurring-payments?execution_date={date}
```

#### Получение ожидающих платежей
```
GET /internal/pending-payments?execution_date={date}
```

#### Повтор неудачного платежа
```
POST /internal/retry-failed-payment/{schedule_id}
```

## Запуск

### Локальная разработка

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Настроить переменные окружения:
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/recurring_db"
export EXPENSE_SERVICE_URL="http://localhost:8003"
export INCOME_SERVICE_URL="http://localhost:8004"
export CATEGORY_SERVICE_URL="http://localhost:8002"
```

3. Выполнить миграции:
```bash
alembic upgrade head
```

4. Запустить сервис:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker-compose up recurring_service
```

## Встроенный шедулер

Сервис имеет встроенный Python шедулер на основе APScheduler, который автоматически запускается при старте приложения.

### Автоматическое выполнение
- **Расписание**: каждый день в 00:01
- **Автозапуск**: при старте сервиса
- **Не требует**: внешних cron jobs

### Управление шедулером

#### Получить статус шедулера
```bash
GET /internal/scheduler/status
```

#### Выполнить платежи сейчас (для тестирования)
```bash
POST /internal/scheduler/execute-now
```

### Альтернатива: Внешний cron

Если нужно использовать внешний cron вместо встроенного шедулера:

```bash
# Выполнять каждый день в 00:01
0 0 * * * curl -X POST http://recurring-service:8000/internal/execute-recurring-payments
```

## Примеры использования

### Создание ежемесячной арендной платы

```json
{
  "name": "Аренда квартиры",
  "description": "Ежемесячная арендная плата",
  "amount": 50000,
  "currency": "RUB",
  "category_id": "123e4567-e89b-12d3-a456-426614174001",
  "payment_type": "expense",
  "schedule_type": "monthly",
  "schedule_config": {
    "day_of_month": 1
  },
  "start_date": "2024-01-01"
}
```

### Создание еженедельной зарплаты

```json
{
  "name": "Зарплата",
  "description": "Еженедельная зарплата",
  "amount": 100000,
  "currency": "RUB",
  "category_id": "123e4567-e89b-12d3-a456-426614174002",
  "payment_type": "income",
  "schedule_type": "weekly",
  "schedule_config": {
    "day_of_week": 5
  },
  "start_date": "2024-01-01"
}
```

## Интеграция

Сервис интегрируется с:
- **expense_service** - для создания расходов
- **income_service** - для создания доходов  
- **category_service** - для валидации категорий

## Мониторинг

- Логирование всех операций
- Отслеживание успешных и неудачных выполнений
- Статистика по пользователям
- Health check endpoints
