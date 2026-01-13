FROM python:3.11-slim

# Install system dependencies including postgresql-client for migrations
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY income_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY income_service/ .

# Copy logging directory
COPY logging/ /app/logging

# Copy and set executable permission for startup script
COPY income_service/startup.sh .
RUN chmod +x startup.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./startup.sh"]
