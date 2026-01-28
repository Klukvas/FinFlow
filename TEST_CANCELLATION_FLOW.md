# Тестирование функции отмены подписки

## 🎯 Где находится кнопка отмены?

Кнопка "Cancel Subscription" (Скасувати підписку / Отменить подписку) появляется в компоненте **SubscriptionLimits** на странице профиля или биллинга.

### Условия показа кнопки:

✅ Показывается когда:
- У пользователя есть платная подписка (Professional или Enterprise)
- `auto_renew = true` (подписка активна, не отменена)

❌ НЕ показывается когда:
- У пользователя план Basic (бесплатный)
- Подписка уже отменена (`auto_renew = false`)

---

## 🧪 Быстрый тест (за 2 минуты)

### Шаг 1: Создайте тестовую подписку

```bash
# Подключитесь к базе данных
docker-compose exec db psql -U postgres -d subscription_db

# Выполните SQL (замените '1' на ваш user_id):
INSERT INTO subscriptions (
    user_id, plan_code, status, started_at, expires_at, 
    next_billing_date, auto_renew, consent_given, 
    consent_version, consent_timestamp, created_at, updated_at
) VALUES (
    '1',  -- ЗАМЕНИТЕ на ваш user_id!
    'professional',
    'active',
    NOW(),
    NOW() + INTERVAL '30 days',
    NOW() + INTERVAL '30 days',
    TRUE,
    TRUE,
    'v1.0.0',
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (user_id) 
DO UPDATE SET
    plan_code = 'professional',
    status = 'active',
    auto_renew = TRUE,
    expires_at = NOW() + INTERVAL '30 days',
    consent_given = TRUE,
    updated_at = NOW();

-- Проверьте подписку:
SELECT user_id, plan_code, status, auto_renew, expires_at 
FROM subscriptions WHERE user_id = '1';
```

### Шаг 2: Откройте страницу с подпиской

1. Залогиньтесь в приложении под пользователем с ID = 1
2. Перейдите на страницу, где отображается компонент `SubscriptionLimits`
3. Вы должны увидеть:
   - Текущий план: **Professional**
   - Кнопку **"Cancel Subscription"** (красная, с иконкой 🚫)
   - Кнопку **"Change Plan"** (градиентная)

### Шаг 3: Протестируйте отмену

1. **Нажмите кнопку "Cancel Subscription"**
2. Откроется модальное окно с:
   - Предупреждением
   - Деталями подписки
   - Двумя опциями:
     - ⭕ **Cancel at end of period** (Рекомендуется) - доступ до конца периода
     - ⭕ **Cancel immediately** - потеря доступа сейчас
   - Опциональным выбором причины
   - Комментарием (опционально)

3. **Выберите "Cancel at end of period"**
4. **Нажмите "Cancel Subscription"** (красная кнопка)

5. **Проверьте результат:**
   - Должен появиться оранжевый баннер: "Subscription Canceled - Access until [DATE]"
   - Кнопка "Cancel Subscription" исчезнет
   - Останется только кнопка "Change Plan"

### Шаг 4: Проверьте в базе данных

```bash
docker-compose exec db psql -U postgres -d subscription_db -c \
  "SELECT user_id, plan_code, status, auto_renew, canceled_at, expires_at, cancellation_reason 
   FROM subscriptions WHERE user_id = '1';"
```

Должны увидеть:
- `status`: `active` (если выбрали "at period end")
- `auto_renew`: **`false`** ← ВАЖНО! Это предотвращает будущие списания
- `canceled_at`: timestamp отмены
- `cancellation_reason`: причина, если указали

---

## 📍 Где найти компонент SubscriptionLimits

Компонент отображается на:
- Странице профиля (Profile page)
- Странице биллинга (Billing page)
- Dashboard (если добавлен)

Проверьте ваш роутинг и добавьте компонент, если его еще нет:

```typescript
import { SubscriptionLimits } from '@/components/ui/subscription/SubscriptionLimits';

// На вашей странице:
<SubscriptionLimits />
```

---

## 🎨 Как выглядит кнопка

```
┌─────────────────────────────────────────────────┐
│  👑 Subscription Limits                        │
│     Your current plan and limits               │
│     Current Plan: Professional                 │
│                                                 │
│  [🚫 Cancel Subscription] [🚀 Change Plan]    │
│   ↑ КРАСНАЯ КНОПКА       ↑ ГРАДИЕНТНАЯ         │
└─────────────────────────────────────────────────┘
```

Если подписка отменена, вместо кнопки "Cancel" появится предупреждение:

```
┌─────────────────────────────────────────────────┐
│  ⚠️ Subscription Canceled                       │
│     You have access until Feb 28, 2026         │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Тестирование полного цикла

### 1. Создать подписку
```sql
-- auto_renew = TRUE
```

### 2. Отменить подписку (через UI)
- Результат: `auto_renew = false`
- Доступ сохраняется до `expires_at`

### 3. Проверить планировщик
```bash
# Запустить scheduler вручную или подождать cron
# Подписка с auto_renew=false должна быть ПРОПУЩЕНА
docker-compose logs scheduler_service | grep "auto_renew_false"
```

Должны увидеть в логах:
```
subscription_canceled_auto_renew_false - SKIPPED
```

---

## ✅ Чеклист готовности

- [ ] Подписка создана в базе (user_id, plan_code='professional', auto_renew=true)
- [ ] Frontend отображает кнопку "Cancel Subscription"
- [ ] Модальное окно открывается при клике
- [ ] Отмена работает (API вызывается)
- [ ] auto_renew меняется на false в базе
- [ ] Показывается баннер "Subscription Canceled"
- [ ] Scheduler пропускает отмененные подписки

---

## 🐛 Если кнопка не видна

**Проблема:** Кнопка "Cancel Subscription" не отображается

**Проверьте:**

1. **Есть ли подписка в базе:**
   ```sql
   SELECT * FROM subscriptions WHERE user_id = '1';
   ```
   Должна вернуть строку с `plan_code != 'basic'`

2. **API возвращает подписку:**
   ```bash
   curl http://localhost:8011/v1/subscriptions/1
   ```
   Должен вернуть JSON с подпиской

3. **Компонент SubscriptionLimits загружает подписку:**
   Откройте DevTools → Console, ищите ошибки

4. **Условие показа кнопки:**
   ```typescript
   const isPaidPlan = subscription && subscription.plan_code !== 'basic';
   const isCanceled = subscription && !subscription.auto_renew;
   // Кнопка показывается если: isPaidPlan && !isCanceled
   ```

---

## 💡 Быстрая команда для теста

Одна команда создаст подписку для user_id=1:

```bash
docker-compose exec db psql -U postgres -d subscription_db -c "INSERT INTO subscriptions (user_id, plan_code, status, started_at, expires_at, next_billing_date, auto_renew, consent_given, consent_version, created_at, updated_at) VALUES ('1', 'professional', 'active', NOW(), NOW() + INTERVAL '30 days', NOW() + INTERVAL '30 days', TRUE, TRUE, 'v1.0.0', NOW(), NOW()) ON CONFLICT (user_id) DO UPDATE SET plan_code='professional', status='active', auto_renew=TRUE, expires_at=NOW() + INTERVAL '30 days', updated_at=NOW();"
```

Затем обновите страницу - кнопка должна появиться! 🎉
