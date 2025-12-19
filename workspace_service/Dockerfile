# Use official Python image
FROM python:3.11-slim

# Install Poetry and postgresql-client for pg_isready
RUN pip install --upgrade pip && pip install poetry \
 && apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies and install
COPY workspace_service/pyproject.toml workspace_service/poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

# Copy application code
COPY workspace_service/ .

# Copy shared logging directory
COPY logging/ /app/logging

# Make startup script executable
RUN chmod +x startup.sh

# Open port and start server via startup script
CMD ["./startup.sh"]

