FROM python:3.10-slim

# Instalar dependencias del sistema y Chrome de forma directa
RUN apt-get update && apt-get install -y wget unzip \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codigo fuente
COPY notificador_bb.py .
COPY cookies.json .

# Ejecutar el bot
CMD ["python", "-u", "notificador_bb.py"]
