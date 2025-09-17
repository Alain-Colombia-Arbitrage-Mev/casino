# Guía de Despliegue - Analizador de Ruleta Vue + Flask

Este documento describe cómo desplegar la aplicación completa (frontend Vue + backend Flask) en diferentes entornos.

## Estructura del Proyecto

```
E:/aicasino2/
├── app.py                  # Aplicación principal de Flask (backend)
├── roulette_analyzer.py    # Módulo con lógica de análisis de ruleta
├── templates/              # Carpeta de plantillas HTML (para versión sin Vue)
└── roulette-analyzer/      # Aplicación Vue (frontend)
    ├── src/                # Código fuente Vue
    ├── dist/               # Compilación de producción (generada con npm run build)
    └── ...
```

## Opciones de Despliegue

### 1. Desarrollo Local (Dos servidores)

En este modo, ejecutamos el frontend y el backend por separado:

```bash
# Terminal 1 - Backend Flask (puerto 5001)
cd E:/aicasino2
python app.py

# Terminal 2 - Frontend Vue (puerto 5173 con proxy a Flask)
cd E:/aicasino2/roulette-analyzer
npm run dev
```

Acceder a: http://localhost:5173

### 2. Desarrollo con un solo comando

Usando el script `start-all` que configura concurrently:

```bash
cd E:/aicasino2/roulette-analyzer
npm run start-all
```

### 3. Producción - Servir frontend desde Flask

En producción, Flask puede servir los archivos estáticos de Vue:

1. Compilar el frontend:

```bash
cd E:/aicasino2/roulette-analyzer
npm run build
```

2. Configurar Flask para servir archivos estáticos desde la carpeta `dist`:

```python
# Añadir a app.py
from flask import send_from_directory

# Configurar para servir archivos estáticos
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path):
    if path and os.path.exists(os.path.join('roulette-analyzer/dist', path)):
        return send_from_directory('roulette-analyzer/dist', path)
    else:
        return send_from_directory('roulette-analyzer/dist', 'index.html')
```

3. Ejecutar solo el servidor Flask:

```bash
cd E:/aicasino2
python app.py
```

Acceder a: http://localhost:5001

### 4. Producción con Docker (Opción avanzada)

Para entornos de producción con Docker:

1. Crear Dockerfile:

```dockerfile
FROM node:18 as build-stage
WORKDIR /app
COPY roulette-analyzer/package*.json ./
RUN npm install
COPY roulette-analyzer/ ./
RUN npm run build

FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py roulette_analyzer.py ./
COPY --from=build-stage /app/dist ./roulette-analyzer/dist

EXPOSE 5001
CMD ["python", "app.py"]
```

2. Crear archivo requirements.txt:

```
flask==2.0.1
flask-cors==3.0.10
requests==2.26.0
supabase==0.0.2
python-dotenv==0.19.0
google-cloud-speech==2.9.0
```

3. Construir y ejecutar la imagen:

```bash
docker build -t roulette-analyzer .
docker run -p 5001:5001 roulette-analyzer
```

Acceder a: http://localhost:5001

## Despliegue en Plataformas Cloud

### Railway

1. Conectar tu repositorio Git
2. Configurar el directorio de compilación para el frontend:
   - Ruta de Compilación: `roulette-analyzer`
   - Comando de Compilación: `npm run build`
   - Directorio de Salida: `dist`
3. Configurar el inicio del backend:
   - Comando de Inicio: `python app.py`
4. Configurar variables de entorno para el backend

### Vercel o Netlify (Solo frontend)

Si prefieres desplegar el frontend y el backend por separado:

1. Desplegar frontend en Vercel/Netlify:
   - Directorio: `roulette-analyzer`
   - Comando de Compilación: `npm run build`
   - Directorio de Salida: `dist`
   - Configurar variables de entorno para la URL de la API

2. Desplegar backend en Railway/Heroku/etc:
   - Servicio solo de backend con CORS configurado para permitir solicitudes del frontend

## Migración a Servicios de Análisis en la Nube

Para mayor escalabilidad, considera migrar partes del análisis a servicios especializados:

- Google Cloud AI Platform para modelos de predicción
- AWS Lambda para análisis bajo demanda
- Azure Functions para procesamiento en tiempo real 