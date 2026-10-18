# Imagen base ligera de Python
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y fuerza logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para compilar psycopg2 y ortools
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiamos primero requirements.txt para aprovechar el cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY . .

EXPOSE 8000

# host 0.0.0.0 es obligatorio dentro de un contenedor (no 127.0.0.1)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
