# Script para limpiar y reiniciar el proyecto Nuxt de manera segura
Write-Host "Limpiando proyecto Nuxt..." -ForegroundColor Cyan

# Detener todos los procesos de Node
Write-Host "Deteniendo procesos de Node..." -ForegroundColor Yellow
taskkill /f /im node.exe 2>$null
# Esperar a que todos los procesos se detengan
Start-Sleep -Seconds 2

# Eliminar directorios de caché y build
Write-Host "Eliminando directorios de caché y build..." -ForegroundColor Yellow
$directories = @('.nuxt', '.output', 'node_modules/.cache', 'node_modules/.vite')

foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "Eliminando $dir..." -ForegroundColor Gray
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        if (-not $?) {
            Write-Host "⚠️ No se pudo eliminar $dir completamente" -ForegroundColor Red
        }
    }
}

# Limpiar caché de npm
Write-Host "Limpiando caché de npm..." -ForegroundColor Yellow
npm cache clean --force

# Reiniciar el servidor de desarrollo
Write-Host "Iniciando servidor de desarrollo..." -ForegroundColor Green
npm run dev 