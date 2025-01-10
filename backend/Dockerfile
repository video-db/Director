FROM python:3.12-slim

WORKDIR /app

COPY . /app/

COPY ./requirements.txt /app/
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Initialize database based on environment variable
COPY ./scripts/init_db.sh /app/
RUN chmod +x /app/scripts/init_db.sh
RUN ./scripts/init_db.sh

EXPOSE 8000 

CMD ["python", "director/entrypoint/api/server.py"]