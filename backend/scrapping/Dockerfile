# Dockerfile para Railway deployment del scraper de ruleta
FROM python:3.11-slim

# Instalar dependencias del sistema para Chrome y PostgreSQL
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements_railway.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements_railway.txt

# Copiar código fuente
COPY roulette_scraper_railway.py .
COPY .env* ./

# Crear directorios necesarios
RUN mkdir -p roulette_data

# Variables de entorno para Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome

# Comando para ejecutar el scraper
CMD ["python", "roulette_scraper_railway.py"] 