# 🦊 DETECTOR FIREFOX INTEGRADO CON MODO INCÓGNITO

## 🎯 ¿Qué es?

El **Detector Firefox Integrado** es la solución perfecta para usuarios que **prefieren Firefox en modo incógnito** para casinos online. Usa Playwright para controlar Firefox directamente con navegación privada por defecto.

## ⚡ Ventajas principales

- **🦊 Optimizado específicamente para Firefox** - No usa Chromium
- **🔒 Modo incógnito por defecto** - Navegación privada automática
- **🎮 Control total del navegador** - Firefox completamente controlado
- **🔍 Detección específica para Firefox** - Selectores optimizados
- **📐 Coordenadas relativas adaptables** - Se ajustan automáticamente
- **✨ Indicadores visuales mejorados** - Mejor feedback en Firefox

## 🚀 Cómo usar

### 1. Iniciar el detector
```bash
npm run detector-firefox
```

### 2. Flujo básico para Firefox
```
🦊 🔒 ¿Qué quieres hacer?
1. "abrir" → Abre Firefox con Lightning Roulette en modo incógnito
2. "detectar" → Detecta números optimizado para Firefox
3. "coordenadas" → Ver números detectados específicos de Firefox
4. "clicks" → Ejecutar clicks directamente en Firefox
```

### 3. Flujo híbrido recomendado
```
1. "abrir" → Abre Firefox en modo incógnito
2. "hibrido" → Detección automática + manual específica para Firefox
3. "clicks" → Ejecutar todos los clicks en Firefox
4. "exportar" → Guardar coordenadas compatibles
```

## 📋 Comandos específicos Firefox

| Comando | Descripción |
|---------|-------------|
| `abrir` | 🦊 Abre Firefox con Lightning Roulette |
| `detectar` | 🔍 Detecta números con selectores específicos Firefox |
| `manual` | 👆 Graba clicks con indicadores rojos optimizados |
| `hibrido` | 🔄 Combina detección automática + manual Firefox |
| `coordenadas` | 📊 Muestra coordenadas detectadas en Firefox |
| `clicks` | 🎯 Ejecuta clicks optimizados para Firefox |
| `exportar` | 💾 Exporta coordenadas desde Firefox |
| `configurar` | ⚙️ Configura tamaño de ventana Firefox |
| `incognito` | 🔒 Alterna modo incógnito (activado por defecto) |
| `cerrar` | 🚪 Cierra Firefox |
| `salir` | 👋 Sale del programa |

## 🔧 Configuración Firefox

### Modo incógnito
- **Por defecto**: 🔒 ACTIVADO
- **Cambiar**: Comando `incognito`
- **Ventaja**: Mayor privacidad para casinos

### Tamaño de ventana
- **Por defecto**: 1280 x 720
- **Modificar**: Comando `configurar`
- **Recomendado**: 1920x1080 para mejor detección

### URL principal configurada
```
🎯 bet20play México: https://bet20play.com/mx/live-casino/game/evolution/lightning_roulette
```

## 💡 Flujos de trabajo específicos

### 🔒 Sesión incógnito completa
```
1. npm run detector-firefox
2. abrir (automáticamente en modo incógnito)
3. [Usa URL de tu casino favorito]
4. hibrido
   - Detección automática optimizada para Firefox
   - Complementa con clicks manuales si es necesario
5. clicks
6. exportar
7. cerrar (cierra Firefox automáticamente)
```

### 🎯 Solo detección manual precisa
```
1. npm run detector-firefox
2. abrir
3. manual
   - Click en números de Firefox
   - Indicadores rojos animados
   - Detección automática del elemento clickeado
4. coordenadas
5. clicks
```

### 🔄 Cambiar de modo incógnito a normal
```
1. npm run detector-firefox
2. incognito (cambia a modo normal)
3. abrir (abre en modo normal)
4. [resto del flujo]
```

## 📊 Detección específica Firefox

### 🤖 Automática optimizada
- **Selectores específicos**: `.roulette-number`, `.betting-spot`, `.numberContainer`
- **Evolution Gaming**: `.betspot`, `.roulette-grid-number`
- **Grid simulado**: Si no encuentra elementos, genera posiciones realistas
- **Apuestas exteriores**: RED, BLACK, EVEN, ODD, docenas

### 👆 Manual con indicadores
- **Indicadores rojos animados**: Círculos rojos con animación de desvanecimiento
- **Detección inteligente**: Múltiples métodos para obtener el valor del número
- **Información de elemento**: Guarda tagName, className, id del elemento
- **Limpieza automática**: Remueve listeners al terminar

### 🔧 Grid simulado Firefox
Si no encuentra elementos específicos del juego:
- **Posiciones optimizadas**: Para resolución típica de Firefox
- **Grid realista**: 3 filas x 12 columnas como Lightning Roulette real
- **Cero especial**: Posición vertical a la izquierda
- **Apuestas exteriores**: Posicionadas correctamente

## 📁 Archivos generados específicos

- `lightning_roulette_firefox_captura.png` - Captura desde Firefox
- `coordenadas_firefox_integrado.json` - Coordenadas específicas Firefox
- Compatible con clicker adaptativo (carga automáticamente)

## 🔗 Integración con otros módulos

### Con clicker adaptativo
```bash
# 1. Detectar con Firefox
npm run detector-firefox
# Usa "exportar" para guardar

# 2. Usar clicker adaptativo  
npm run clicker-adaptativo
# Carga automáticamente coordenadas de Firefox
```

### Formato de exportación
```json
{
  "timestamp": "2024-01-01T00:00:00.000Z",
  "navegador": "firefox",
  "modoIncognito": true,
  "metodo": "firefox_integrado",
  "dimensiones": { "width": 1280, "height": 720 },
  "elementos": [...],
  "estadisticas": {
    "total": 44,
    "numeros": 37,
    "apuestas": 7,
    "automaticos": 30,
    "manuales": 14
  }
}
```

## ⚠️ Requisitos Firefox

- **Node.js** 16+
- **Playwright** (incluido en dependencias)
- **Firefox** instalado en el sistema
- **Conexión a internet** para cargar Lightning Roulette

### Primera instalación
```bash
# Si es la primera vez usando Playwright con Firefox:
npx playwright install firefox
```

## 🐛 Solución de problemas Firefox

### Firefox no abre
```bash
# Verificar Firefox instalado
firefox --version

# Instalar Firefox para Playwright
npx playwright install firefox

# Reinstalar Playwright si es necesario
npm install playwright --force
```

### Error de conexión en Firefox
- **URLs específicas**: Usa las URLs sugeridas optimizadas para Firefox
- **Permisos**: Firefox puede pedir permisos adicionales para algunos sitios
- **Extensiones**: El modo incógnito puede bloquear algunas extensiones
- **Certificados**: Algunos casinos requieren certificados específicos

### No detecta números en Firefox
- **Usar modo "hibrido"**: Más preciso que solo "detectar"
- **Grabación manual**: Siempre funciona con indicadores visuales
- **Grid simulado**: Se activa automáticamente como respaldo
- **Esperar carga**: Firefox puede necesitar más tiempo para cargar

### Clicks no funcionan en Firefox
- **Verificar carga completa**: Esperar que Lightning Roulette esté totalmente cargado
- **Pausas variables**: Los clicks incluyen pausas humanas automáticas
- **Modo incógnito**: Verificar si el sitio funciona en modo incógnito
- **Coordenadas**: Verificar con comando "coordenadas"

## 💡 Consejos específicos Firefox

1. **🔒 Modo incógnito siempre**: Mejor para casinos online
2. **🦊 URLs optimizadas**: Usa las URLs sugeridas específicas para Firefox
3. **⏰ Tiempo de carga**: Firefox puede necesitar más tiempo que Chrome
4. **🎯 Grabación manual**: Los indicadores rojos son más visibles en Firefox
5. **📐 Resolución**: 1920x1080 da mejores resultados de detección
6. **🔄 Combinar métodos**: Híbrido es más preciso que solo automático

## 🔄 Comparación Firefox vs otros navegadores

| Característica | Firefox Integrado | Chromium Integrado | Detector Híbrido |
|---------------|-------------------|-------------------|------------------|
| **Privacidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Modo incógnito** | 🔒 Por defecto | ⚙️ Configurable | ❌ No disponible |
| **Detección optimizada** | 🦊 Firefox específico | 🌐 Chrome específico | 🔧 Generic |
| **Control total** | ✅ Completo | ✅ Completo | ❌ Limitado |
| **Indicadores visuales** | ✨ Animados | ⚪ Básicos | ❌ No disponible |
| **Compatibilidad casino** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🏆 ¿Cuándo usar Firefox integrado?

**✅ Ideal para:**
- Usuarios que prefieren Firefox
- Navegación en modo incógnito por defecto
- Casinos que funcionan mejor en Firefox
- Mayor privacidad y seguridad
- Detección específica optimizada para Firefox

**⚠️ Considera alternativas si:**
- Firefox no está instalado
- Prefieres Chrome/Chromium
- El casino funciona mejor en Chrome
- Necesitas máxima velocidad de ejecución

**🏆 Recomendación**: Firefox integrado es la mejor opción para usuarios que priorizan privacidad y usan Firefox habitualmente. 