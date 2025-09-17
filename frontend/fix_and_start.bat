@echo off
echo ========================================
echo   ARREGLANDO Y INICIANDO FRONTEND
echo ========================================

cd /d "%~dp0"

echo.
echo 1. Limpiando cache y directorios...
rmdir /s /q .nuxt 2>nul
rmdir /s /q .output 2>nul
rmdir /s /q node_modules 2>nul

echo.
echo 2. Limpiando cache de npm...
call npm cache clean --force

echo.
echo 3. Instalando dependencias...
call npm install

echo.
echo 4. Verificando instalacion de Nuxt...
call npm list nuxt

echo.
echo 5. Iniciando servidor de desarrollo...
call npm run dev

pause