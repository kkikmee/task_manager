# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Системные зависимости (нужны для psycopg2 и Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Зависимости Python — отдельным слоем для кеширования
COPY taskManager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY taskManager/ .

# Создаём папки для медиа и статики
RUN mkdir -p /app/media /app/staticfiles

# Порт
EXPOSE 8000

# Entrypoint: миграции + collectstatic + запуск gunicorn
CMD ["sh", "-c", \
     "python manage.py migrate --no-input && \
      python manage.py collectstatic --no-input && \
      gunicorn taskManager.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
