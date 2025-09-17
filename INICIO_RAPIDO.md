# 🚀 INICIO RÁPIDO - Sistema Automático de Ruleta

## ⚡ **Ejecutar TODO con UNA SOLA LÍNEA**

### 🖥️ **Windows - Opción 1 (Recomendada)**
```cmd
start_system.bat
```

### 🖥️ **Windows - Opción 2 (PowerShell)**
```powershell
powershell -ExecutionPolicy Bypass -File start_system.ps1
```

### 🐧 **Linux/Mac**
```bash
chmod +x start_system.sh && ./start_system.sh
```

### 🐍 **Multiplataforma (Python)**
```bash
python iniciar_sistema_completo.py
```

### 📦 **Con NPM (Requiere instalación previa)**
```bash
npm install && npm run dev
```

---

## 🔧 **¿Qué hace cada script?**

### **start_system.bat** (Windows)
- ✅ Verifica dependencias (Redis, Python, Node.js)
- 📦 Instala automáticamente si faltan
- 🚀 Inicia todos los servicios en ventanas separadas
- 🌐 Abre el navegador automáticamente
- 🛑 Permite detener todo desde una ventana

### **start_system.ps1** (PowerShell)
- 🎨 Interfaz colorida y moderna
- 🔍 Verificación avanzada de dependencias
- ⚡ Gestión inteligente de procesos
- 🔒 Manejo seguro de errores

### **start_system.sh** (Unix)
- 🐧 Compatible con Linux/Mac
- 🎯 Detección automática del sistema operativo
- 🔄 Gestión automática de procesos
- 🧹 Limpieza completa al salir

### **iniciar_sistema_completo.py** (Python)
- 🌍 Multiplataforma (Windows/Linux/Mac)
- 🧠 Lógica inteligente de configuración
- 🎨 Logging colorido y detallado
- 🔧 Configuración automática del entorno

---

## 📋 **Requisitos Previos**

### 📥 **Instalar Dependencias**

#### **Redis**
- **Windows**: 
  - Descarga: https://github.com/tporadowski/redis/releases
  - O usar Chocolatey: `choco install redis-64`
- **Linux**: `sudo apt-get install redis-server`
- **Mac**: `brew install redis`

#### **Python 3.7+**
- Descarga: https://python.org/downloads

#### **Node.js 16+**
- Descarga: https://nodejs.org/download

---

## 🎯 **Flujo Completo Automático**

1. **🔍 Verificación**: Scripts verifican dependencias
2. **📦 Instalación**: Se instalan automáticamente paquetes faltantes
3. **⚙️ Configuración**: Se crea archivo `.env` si no existe
4. **🚀 Inicio Secuencial**:
   - Redis Server (Puerto 6379)
   - Backend API (Puerto 5000)
   - Frontend Web (Puerto 3000)
5. **🌐 Apertura**: Navegador se abre automáticamente
6. **▶️ Activación**: Ve a "Sistema Automático" → "Iniciar Sistema"

---

## 🔗 **Accesos Directos**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/automatic-service/status
- **Estado Redis**: `redis-cli ping`

---

## 🛑 **Detener el Sistema**

- **Windows**: Presiona cualquier tecla en la ventana principal
- **Unix**: Presiona `Ctrl+C`
- **Emergencia**: Cierra todas las ventanas de terminal

---

## ⚠️ **Solución de Problemas**

### **Error: "Redis no encontrado"**
```bash
# Windows
choco install redis-64

# Linux
sudo apt-get install redis-server

# Mac
brew install redis
```

### **Error: "Python no encontrado"**
- Instala Python desde: https://python.org/downloads
- Asegúrate de marcar "Add to PATH"

### **Error: "Node.js no encontrado"**
- Instala Node.js desde: https://nodejs.org
- Reinicia tu terminal después de instalar

### **Error: "Puerto ocupado"**
```bash
# Verificar puertos ocupados
netstat -ano | findstr :3000
netstat -ano | findstr :5000
netstat -ano | findstr :6379

# Matar procesos si es necesario
taskkill /F /PID [número_de_proceso]
```

---

## 🎮 **Uso del Sistema**

1. **Ejecuta** cualquiera de los scripts de arriba
2. **Espera** a que aparezca "✅ SISTEMA INICIADO CORRECTAMENTE"
3. **Ve** al navegador (se abre automáticamente)
4. **Clic** en la pestaña "🤖 Sistema Automático"
5. **Presiona** el botón "Iniciar Sistema"
6. **¡Disfruta!** del sistema automático funcionando

---

## 🏆 **Características del Sistema**

- 🤖 **Detección Automática** de números
- 🧠 **Predicciones con IA** avanzada
- 📊 **Estadísticas en Tiempo Real**
- 🎯 **Evaluación Automática** de predicciones
- 📱 **Interfaz Web Moderna**
- ⚡ **Actualizaciones Cada 3 Segundos**
- 🎨 **UI Responsiva y Atractiva**

---

## 🔄 **Actualizaciones**

Para obtener las últimas actualizaciones:
```bash
git pull origin main
```

Luego ejecuta cualquiera de los scripts de inicio. 