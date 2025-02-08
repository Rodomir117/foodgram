#!/bin/bash

# Запуск миграций
python manage.py migrate
# Загрузка данных из CSV-файлов в базу данных
python manage.py load_db
# Сборка статики 
python manage.py collectstatic --noinput
# Копирование собранной статики
cp -r /app/collected_static/. /backend_static/static/

exec "$@"
# Запуск Gunicorn
# exec gunicorn --bind 0.0.0.0:7000 foodgram_backend.wsgi