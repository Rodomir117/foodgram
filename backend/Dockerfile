FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

COPY /entrypoint.prod.sh /entrypoint.prod.sh
RUN chmod +x /entrypoint.prod.sh
ENTRYPOINT ["/entrypoint.prod.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:7070", "foodgram_backend.wsgi"]