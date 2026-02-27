FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir "poetry==1.8.3"

WORKDIR /app

COPY ai_assistant_service/pyproject.toml ai_assistant_service/poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-interaction --no-ansi

# Install shared library
COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY ai_assistant_service/ .

RUN adduser --disabled-password --gecos "" appuser && chmod +x startup.sh
USER appuser

CMD ["./startup.sh"]
