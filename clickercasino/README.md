# 🤖 Ghost Roulette AI - Clicker Inteligente

Un sistema de automatización avanzado para juegos de ruleta usando inteligencia artificial y técnicas anti-detección.

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
npm install
```

### 2. Ejecutar el clicker

#### Modo Demo (Recomendado para empezar)
```bash
npm run demo
```

#### Otras configuraciones disponibles:
```bash
npm run prueba     # Configuración básica de prueba
npm run bet365     # Configuración para Bet365
npm run evolution  # Configuración para Evolution Gaming
npm run sigiloso   # Modo completamente oculto
```

### 3. Configuración personalizada

Para usar tu propia URL y números, edita el archivo `configurar_clicker.js`:

```javascript
const miConfiguracion = {
    url: 'https://tu-casino.com/ruleta',
    targetNumbers: [7, 14, 21],  // Números que quieres clickear
    headless: false,             // true = sin ventana, false = con ventana
    showReport: true            // Mostrar reporte final
};
```

## 🎯 Características

- **🧠 IA Avanzada**: Simula comportamiento humano realista
- **👻 Anti-Detección**: Técnicas avanzadas para evitar detección
- **🎭 Personalidades**: Simula diferentes tipos de jugadores
- **🔍 Detección Inteligente**: Múltiples estrategias para encontrar números
- **📊 Reportes Detallados**: Análisis completo de la sesión

## 🛠️ Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `npm start` | Ejecuta con configuración por defecto |
| `npm run demo` | Modo demostración |
| `npm run prueba` | Configuración de prueba |
| `npm run bet365` | Configuración para Bet365 |
| `npm run evolution` | Configuración para Evolution Gaming |
| `npm run sigiloso` | Modo completamente oculto |

## ⚙️ Configuración Avanzada

### Personalizar números objetivo
Edita `targetNumbers` en cualquier configuración:
```javascript
targetNumbers: [0, 7, 14, 21, 28, 35]  // Tus números favoritos
```

### Cambiar URL del casino
```javascript
url: 'https://tu-casino-favorito.com/ruleta'
```

### Modo headless (sin ventana)
```javascript
headless: true  // Para ejecutar en segundo plano
```

## 🤖 Tipos de Personalidades AI

El sistema simula diferentes tipos de jugadores:

- **Carlos (Conservador)**: Jubilado, juego cauteloso, decisiones lentas
- **Sofia (Agresivo)**: Joven profesional, decisiones rápidas, apuestas arriesgadas
- **Miguel (Estratégico)**: Empresario experimentado, análisis antes de apostar

## 🛡️ Seguridad y Anti-Detección

- User agents dinámicos y realistas
- Patrones de movimiento de mouse humanos
- Tiempos de reacción naturales
- Fingerprinting protection
- Headers HTTP auténticos
- Comportamiento adaptativo

## 🐛 Solución de Problemas

### El clicker no abre:
1. Verifica que Node.js esté instalado: `node --version`
2. Instala dependencias: `npm install`
3. Ejecuta: `npm run demo`

### Error de "Cannot find module":
```bash
npm install
```

### Error de conexión:
- Verifica tu conexión a internet
- Prueba con otra URL
- Usa modo `headless: false` para ver qué pasa

### El clicker no encuentra los números:
- La página puede tener una estructura diferente
- Intenta con otra configuración
- Verifica que la URL sea correcta

## 📝 Logs y Debugging

El sistema muestra información detallada:
- 🤖 Estado del AI
- 🎯 Números detectados
- ✅/❌ Resultados de clicks
- 📊 Reportes de sesión

## ⚠️ Advertencias

- Solo para uso educativo y de prueba
- Respeta los términos de servicio de los sitios web
- Usa responsablemente
- No garantizamos resultados en casinos reales

## 🔧 Desarrollo

### Estructura del proyecto:
- `cicker.js` - Clases principales del AI
- `main.js` - Script principal
- `configurar_clicker.js` - Configuraciones preestablecidas
- `package.json` - Dependencias y scripts

### Añadir nuevas configuraciones:
```javascript
// En configurar_clicker.js
miNuevaConfig: {
    url: 'https://ejemplo.com',
    targetNumbers: [1, 2, 3],
    headless: false,
    showReport: true
}
```

## 📚 Documentación Adicional

Para más detalles técnicos, consulta `README_INCOGNITO.md`.

---

**Desarrollado con ❤️ por ClickerCasino** 