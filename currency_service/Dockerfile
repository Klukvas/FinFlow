FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY currency_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY currency_service/ .

# Copy logging directory
COPY logging/ /app/logging

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
