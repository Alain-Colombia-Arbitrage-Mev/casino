#!/usr/bin/env node
/**
 * Script para iniciar el frontend sin HMR (Hot Module Replacement)
 * Útil cuando hay problemas con WebSocket connections
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Iniciando frontend sin HMR...');

// Configurar variables de entorno para deshabilitar HMR
const env = {
  ...process.env,
  NODE_ENV: 'development',
  NUXT_DEVTOOLS_ENABLED: 'false',
  VITE_HMR: 'false',
  HMR: 'false'
};

// Iniciar Nuxt con configuración sin HMR
const nuxtProcess = spawn('npx', ['nuxt', 'dev', '--no-hmr'], {
  cwd: __dirname,
  env: env,
  stdio: 'inherit',
  shell: true
});

nuxtProcess.on('error', (error) => {
  console.error('❌ Error iniciando frontend:', error);
  process.exit(1);
});

nuxtProcess.on('close', (code) => {
  console.log(`Frontend terminado con código: ${code}`);
  process.exit(code);
});

// Manejar señales para limpieza
process.on('SIGINT', () => {
  console.log('\n🛑 Deteniendo frontend...');
  nuxtProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Terminando frontend...');
  nuxtProcess.kill('SIGTERM');
});