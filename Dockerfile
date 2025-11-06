FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=banking_system.settings

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs

RUN python manage.py migrate --noinput || true
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
