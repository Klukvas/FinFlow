FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY goals_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shared library
COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

# Copy application code
COPY goals_service/ .


# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Make startup script executable
RUN chmod +x startup.sh

# Expose port
EXPOSE 8000

# Run the application
CMD ["/bin/bash", "/app/startup.sh"]
