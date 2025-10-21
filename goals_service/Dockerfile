FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY goals_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY goals_service/ .

# Copy logging directory
COPY logging/ /app/logging

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Make startup script executable
RUN chmod +x startup.sh

# Run the application
CMD ["./startup.sh"]
