# Usamos una imagen oficial y ligera de Python
FROM python:3.11-slim

# Evitamos que Python genere archivos .pyc y que almacene en búfer la salida de la consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos FFmpeg y las dependencias esenciales del sistema operativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos las dependencias de Python
COPY cookies.txt .
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de nuestro proyecto al contenedor
COPY . .

# Comando por defecto para ejecutar el bot
CMD ["python", "bot.py"]