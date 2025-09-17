# Script para limpiar y iniciar el frontend
Write-Host "Limpiando directorios de Nuxt..." -ForegroundColor Yellow

# Detener cualquier proceso que pueda estar usando los archivos
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Esperar un momento
Start-Sleep -Seconds 2

# Intentar eliminar directorios problemáticos
$directories = @(".nuxt", ".output")

foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "Eliminando $dir..." -ForegroundColor Cyan
        try {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction Stop
            Write-Host "OK: $dir eliminado" -ForegroundColor Green
        }
        catch {
            Write-Host "WARN: No se pudo eliminar $dir completamente" -ForegroundColor Yellow
        }
    }
}

Write-Host "Reinstalando dependencias..." -ForegroundColor Yellow
npm install --force

Write-Host "Iniciando servidor de desarrollo..." -ForegroundColor Green
npm run dev