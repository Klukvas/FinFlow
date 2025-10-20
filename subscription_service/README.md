subscription_service
====================

FastAPI service managing plans, features, plan-feature rules, and user subscriptions. Provides cached entitlements and publishes subscription change events.

Run locally
-----------

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r subscription_service/requirements.txt
export SUBS_DB_HOST=localhost SUBS_DB_USER=postgres SUBS_DB_PASSWORD=postgres SUBS_DB_NAME=subscription_db
export SUBS_REDIS_URL=redis://localhost:6379/0
cd subscription_service && alembic upgrade head && uvicorn app.main:app --reload --port 8080
```

API
---
- GET `/v1/plans`
- POST `/v1/subscriptions/{user_id}:set_plan` (Idempotency-Key header)
- GET `/v1/entitlements/{user_id}`

Events
------
- `user.subscription.changed` payload: `{ user_id, plan_code, status, expires_at, version }`

Errors
------
All errors follow:

```json
{ "error": "<message>", "errorCode": "@subscription_service/<CODE>" }
```


