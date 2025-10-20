#!/bin/bash

# Скрипт для обновления SSL конфигурации
echo "🔒 Обновление SSL конфигурации для finflow.ltd..."

# Проверяем, что сертификаты существуют
if [ ! -f "/etc/ssl/cf-origin/finflow.crt" ]; then
    echo "❌ Ошибка: Сертификат /etc/ssl/cf-origin/finflow.crt не найден"
    exit 1
fi

if [ ! -f "/etc/ssl/cf-origin/finflow.key" ]; then
    echo "❌ Ошибка: Приватный ключ /etc/ssl/cf-origin/finflow.key не найден"
    exit 1
fi

echo "✅ Сертификаты найдены"

# Проверяем права доступа к сертификатам
if [ ! -r "/etc/ssl/cf-origin/finflow.crt" ] || [ ! -r "/etc/ssl/cf-origin/finflow.key" ]; then
    echo "⚠️  Предупреждение: Проверьте права доступа к сертификатам"
    echo "   Рекомендуется: chmod 644 /etc/ssl/cf-origin/finflow.crt"
    echo "   Рекомендуется: chmod 600 /etc/ssl/cf-origin/finflow.key"
fi

# Перезапускаем Caddy с новой конфигурацией
echo "🔄 Перезапуск Caddy..."
docker-compose -f docker-compose.yml restart caddy

# Проверяем статус
echo "📊 Проверка статуса сервисов..."
docker-compose -f docker-compose.yml ps

echo "✅ SSL конфигурация обновлена!"
echo "🌐 Ваш сайт теперь доступен по адресу: https://finflow.ltd"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте, что DNS запись для finflow.ltd указывает на ваш сервер"
echo "2. Убедитесь, что порты 80 и 443 открыты в файрволе"
echo "3. Проверьте работу сайта: curl -I https://finflow.ltd"
