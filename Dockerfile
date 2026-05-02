# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY taskManager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY taskManager/ .

RUN mkdir -p /app/media /app/staticfiles

EXPOSE 8000

CMD ["sh", "-c", \
     "python manage.py migrate --no-input && \
      python manage.py collectstatic --no-input && \
      gunicorn taskManager.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
