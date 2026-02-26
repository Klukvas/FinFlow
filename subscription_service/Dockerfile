FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY subscription_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install shared library
COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY subscription_service/app /app/app
COPY subscription_service/alembic /app/alembic
COPY subscription_service/alembic.ini /app/alembic.ini
COPY subscription_service/startup.sh /app/startup.sh

RUN chmod +x /app/startup.sh

EXPOSE 8080

CMD ["/app/startup.sh"]


