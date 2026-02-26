FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY scheduler_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shared library
COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

# Copy application code
COPY scheduler_service/app /app/app
COPY scheduler_service/alembic /app/alembic
COPY scheduler_service/alembic.ini /app/alembic.ini
COPY scheduler_service/startup.sh /app/startup.sh

# Create non-root user
RUN useradd -m -u 1000 scheduler && chown -R scheduler:scheduler /app
USER scheduler

# Expose port for health checks and metrics
EXPOSE 8090

# Run startup script
CMD ["bash", "startup.sh"]
