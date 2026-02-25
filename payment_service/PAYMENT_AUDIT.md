# Payment System Audit

## 1. Идемпотентность платежей ✅ IMPLEMENTED

### Текущая реализация:

**Payment Creation (API):**
- ✅ Idempotency-Key header support (`payment_service/app/utils/idempotency.py`)
- ✅ Request hash comparison (same key + different body = 409 Conflict)
- ✅ Cached response return for duplicate requests
- ✅ TTL для idempotency keys (configurable)

**Webhook (Callback):**
- ✅ `has_callback_been_processed()` check by `provider_event_id`
- ✅ `provider_event_id = f"{order_reference}_{transactionStatus}_{createdDate}"` - unique per event
- ✅ Returns existing payment without re-processing

```python
# payment_service.py:176-189
if self.event_repo.has_callback_been_processed(payment.id, provider_event_id, payload_hash):
    logger.info(f"Callback already processed for payment {payment.id}")
    return payment  # Return existing, don't process again
```

### Риски:
- ⚠️ **LOW RISK**: Payload hash comparison is not fully implemented in `has_callback_been_processed`

### TODO:
- [ ] Implement full payload hash comparison as backup

---

## 2. Webhook как единственный источник истины ✅ IMPLEMENTED

### Текущая реализация:

**Webhook через 5 минут:**
- ✅ Works fine - webhook updates payment status whenever it arrives

**Webhook приходит 3 раза:**
- ✅ Idempotency check prevents duplicate processing (see point 1)

**Webhook не приходит вообще:**
- ✅ Reconciliation service exists (`SCHEDULER_TODO.md`)
- ✅ `verify_payment_status()` API call to Paddle CHECK_STATUS
- ⚠️ **NOT AUTOMATED**: Cron job not set up yet

### Risks:
- ⚠️ **MEDIUM RISK**: If notification to subscription_service fails, no retry mechanism

```python
# payment_service.py:250-255
if not success:
    logger.error(f"Failed to notify subscription_service about payment {payment.id}")
    # In production: store in outbox for retry  <-- NOT IMPLEMENTED
```

### TODO:
- [ ] Implement outbox pattern for subscription notifications
- [ ] Set up cron job for reconciliation
- [ ] Add alerting for failed notifications

---

## 3. Машина состояний подписки ⚠️ PARTIAL

### Текущая реализация:

**Состояния:**
```
Subscription.status: 'active' | 'past_due' | 'canceled' | 'paused'
```

**Transitions:**
- ✅ New → Active (via payment)
- ✅ Active → Canceled (via cancel endpoint)
- ⚠️ **MISSING**: Trial state
- ⚠️ **MISSING**: Active → Past_due (on failed renewal)
- ⚠️ **MISSING**: Past_due → Canceled (after grace period)

**Upgrade/Downgrade:**
- ✅ Different plan = new period from NOW
- ✅ Same plan renewal = extend from expires_at

**Cancel:**
- ✅ Cancel at period end (keeps benefits until expires_at)
- ⚠️ **MISSING**: Cancel now (immediate, with prorated refund)

### Risks:
- ⚠️ **MEDIUM RISK**: No trial period support
- ⚠️ **MEDIUM RISK**: No past_due state handling

### TODO:
- [ ] Add trial period support
- [ ] Implement past_due state on failed renewal
- [ ] Add cancel_now option with prorated refund

---

## 4. Retry и Grace Period ❌ NOT IMPLEMENTED

### Текущая реализация:
- ❌ No automatic retry on failed payment
- ❌ No grace period logic
- ❌ No dunning (reminder emails)

### Risks:
- 🔴 **HIGH RISK**: Failed renewal = immediate loss of access (no grace period)
- 🔴 **HIGH RISK**: No automatic retry = lost revenue

### TODO:
- [ ] Add recurring payment support (save recToken from Paddle)
- [ ] Implement retry logic (3 attempts over 7 days)
- [ ] Add grace period (e.g., 7 days of access after expiry)
- [ ] Send dunning emails

---

## 5. Refund ≠ Cancel ⚠️ PARTIAL

### Текущая реализация:

**Payment Status:**
```python
class PaymentStatus(str, enum.Enum):
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
```

**Refund Endpoint:**
- ⚠️ Placeholder only - not fully implemented

```python
# internal.py - refund endpoint
# TODO: Implement actual refund via Paddle API
```

**Webhook:**
- ✅ "Refunded" status from Paddle is mapped to REFUNDED

**Problem:**
- ❌ Refund does NOT automatically cancel subscription
- ❌ Chargeback handling not implemented

### Risks:
- 🔴 **HIGH RISK**: Refund = money gone, subscription still active
- 🔴 **HIGH RISK**: No chargeback handling

### TODO:
- [ ] Implement actual refund via Paddle API
- [ ] On refund → cancel subscription OR downgrade to free
- [ ] Add chargeback webhook handling
- [ ] Add chargeback alerting

---

## 6. Хранение и расчёт денег ✅ GOOD

### Текущая реализация:

```python
# models.py:83
amount = Column(Numeric(10, 2), nullable=False)
```

- ✅ Uses `Numeric(10, 2)` - NOT float
- ✅ Uses `Decimal` in Python code
- ✅ Currency stored as 3-char string (UAH, USD, EUR)

### Risks:
- ⚠️ **LOW RISK**: No proration calculation implemented
- ⚠️ **LOW RISK**: No multi-currency conversion

### TODO:
- [ ] Add proration logic for upgrades
- [ ] Consider storing amounts in cents (integer) for even better precision

---

## 7. Reconciliation (сверка с PSP) ⚠️ PARTIAL

### Текущая реализация:

**Code exists:**
- ✅ `PaddleClient.verify_payment_status()` - CHECK_STATUS API
- ✅ Reconciliation logic documented in `SCHEDULER_TODO.md`

**Not automated:**
- ❌ No cron job set up
- ❌ No nightly reconciliation report
- ❌ No alerting on mismatches

### Risks:
- ⚠️ **MEDIUM RISK**: Lost webhooks not automatically detected

### TODO:
- [ ] Set up cron job for reconciliation (every 5-10 min)
- [ ] Add nightly full reconciliation report
- [ ] Alert on status mismatches

---

## 8. Безопасность и подмена событий ✅ GOOD

### Текущая реализация:

**Webhook Signature Verification:**
```python
# paddle_client.py (webhook signature verification)
def verify_callback_signature(self, callback_data: dict[str, Any]) -> bool:
    # HMAC verification with merchant secret key
    signature_fields = [merchantAccount, orderReference, amount, currency, ...]
    return self.verify_signature(merchant_signature, signature_fields)
```

- ✅ HMAC signature verification
- ✅ Invalid signature → reject webhook
- ✅ Subscription activation only via webhook (not from frontend)

**Internal Service Auth:**
```python
# X-Internal-Token header for service-to-service calls
def verify_internal_token(x_internal_token: str = Header(...)):
    if x_internal_token != settings.internal_secret_token:
        raise AuthError("Invalid internal token")
```

### Risks:
- ⚠️ **LOW RISK**: No IP whitelist for Paddle webhooks
- ⚠️ **LOW RISK**: No rate limiting on webhook endpoint

### TODO:
- [ ] Add IP whitelist for Paddle (optional, signature is enough)
- [ ] Add rate limiting on webhook endpoint

---

## 9. Отмена подписки и UX ⚠️ PARTIAL

### Текущая реализация:

**Backend:**
- ✅ Cancel endpoint exists
- ✅ User keeps access until expires_at
- ✅ canceled_at timestamp stored

**Frontend:**
- ⚠️ **UNKNOWN**: Need to check if cancel confirmation exists
- ⚠️ **UNKNOWN**: Need to check if expiry date is shown

**Notifications:**
- ❌ No email on subscription cancellation
- ❌ No email on upcoming expiry
- ❌ No email on successful payment

### Risks:
- ⚠️ **MEDIUM RISK**: User confusion about when subscription ends
- ⚠️ **MEDIUM RISK**: No confirmation could lead to accidental cancels
- ⚠️ **MEDIUM RISK**: No emails = chargebacks from confused users

### TODO:
- [ ] Add cancel confirmation modal
- [ ] Show clearly when subscription will end
- [ ] Send email on: payment success, cancellation, upcoming expiry
- [ ] Add "reactivate" option for canceled subscriptions

---

# Summary

| Area | Status | Priority |
|------|--------|----------|
| 1. Idempotency | ✅ Good | - |
| 2. Webhook as source of truth | ⚠️ Partial | Medium |
| 3. Subscription state machine | ⚠️ Partial | Medium |
| 4. Retry & Grace period | ❌ Missing | **HIGH** |
| 5. Refund ≠ Cancel | ⚠️ Partial | **HIGH** |
| 6. Money storage | ✅ Good | - |
| 7. Reconciliation | ⚠️ Partial | Medium |
| 8. Security | ✅ Good | Low |
| 9. Cancel UX | ⚠️ Partial | Medium |

## High Priority Fixes:

1. **Refund → Cancel subscription** - prevent "money refunded but subscription active"
2. **Retry logic** - implement recurring payments with recToken
3. **Grace period** - don't immediately cut access on expiry
4. **Outbox pattern** - ensure subscription_service notifications are delivered
