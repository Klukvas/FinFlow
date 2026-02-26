FROM python:3.11-slim

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установить рабочую директорию
WORKDIR /app

# Копировать файлы зависимостей
COPY recurring_service/requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Install shared library
COPY shared/ /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

# Копировать исходный код
COPY recurring_service/ .


# Создать пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открыть порт
EXPOSE 8000

# Make startup script executable
RUN chmod +x startup.sh

# Команда запуска
CMD ["./startup.sh"]
