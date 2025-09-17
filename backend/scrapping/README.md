# 🎰 Casino Bot - Proyecto Limpio

Este proyecto contiene dos scripts principales para automatización de casino:

## 📁 Estructura del Proyecto

```
scrapping/
├── 🎯 script2_mejorado.py      # SCRIPT PRINCIPAL - Clicker automático
├── 📊 roulette_scraper.py      # SCRIPT PRINCIPAL - Scraper de ruleta
├── ⚙️ casino_bot_config.json   # Configuración del bot
├── 📋 requirements.txt         # Dependencias de Python
├── 📁 roulette_data/          # Datos del scraper
│   ├── roulette_numbers.json
│   ├── processed_numbers.txt
│   └── roulette_scraper.log
├── 📄 roulette_bot.log        # Log del clicker
├── 📄 roulette_scraper.log    # Log del scraper
└── 📖 README.md               # Este archivo
```

## 🚀 Scripts Principales

### 1. **script2_mejorado.py** - Clicker Automático
- **Función**: Bot para hacer clicks automáticos en casino
- **Características**:
  - Control por hotkeys (F1, F2, etc.)
  - Múltiples perfiles de juego
  - Apuestas rápidas y múltiples
  - Modo turbo para clicks ultra-rápidos
  - Integración con Firefox

### 2. **roulette_scraper.py** - Scraper de Ruleta
- **Función**: Extrae números de ruleta automáticamente
- **Características**:
  - Scraping con Selenium
  - Almacenamiento en JSON
  - Integración con Supabase
  - Logs detallados
  - Procesamiento automático

## 📦 Instalación

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno** (para el scraper):
   ```bash
   # Crear archivo .env con:
   LOGIN_URL=tu_url_de_login
   DASHBOARD_URL=tu_url_del_dashboard
   ROULETTE_USERNAME=tu_usuario
   ROULETTE_PASSWORD=tu_contraseña
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_KEY=tu_key_de_supabase
   ```

## 🎮 Uso

### Ejecutar el Clicker:
```bash
python script2_mejorado.py
```

### Ejecutar el Scraper:
```bash
python roulette_scraper.py
```

## ⌨️ Controles del Clicker

- **F1**: Guardar posición del cursor
- **F2**: Empezar/parar clicks automáticos
- **F3**: Apuesta rápida en números favoritos
- **F4**: Apuesta múltiple
- **F5**: Modo turbo ON/OFF
- **F6**: Cambio rápido de perfil
- **Ctrl+Q**: Salir del programa

## 🔧 Configuración

El archivo `casino_bot_config.json` almacena:
- Perfiles de juego
- Posiciones guardadas
- Números favoritos
- Configuraciones específicas

## 📊 Logs

- **roulette_bot.log**: Actividad del clicker
- **roulette_scraper.log**: Actividad del scraper
- **roulette_data/**: Todos los datos extraídos

## ⚠️ Notas Importantes

1. **Pillow instalado**: Resuelve el error "No module named 'PIL'"
2. **Firefox requerido**: Para el clicker automático
3. **Chrome requerido**: Para el scraper
4. **Permisos de Windows**: Algunos controles requieren permisos elevados

## 🛠️ Troubleshooting

- **Error PIL**: Ya resuelto con Pillow en requirements.txt
- **Error de permisos**: Ejecutar como administrador
- **Selenium error**: Verificar que Chrome/Firefox estén instalados
- **Hotkeys no funcionan**: Verificar que keyboard esté instalado

---

✅ **Proyecto limpio y organizado** - Solo archivos esenciales 