FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        iputils-ping netcat-openbsd curl procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/backups/clinica \
    && cp backup_clientes_2024.csv /var/backups/clinica/ \
    && python init_db.py \
    && mkdir -p documentos \
    && chown -R www-data:www-data /app /var/backups/clinica

EXPOSE 5000

USER www-data

CMD ["python", "app.py"]
