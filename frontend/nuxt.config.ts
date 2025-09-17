// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  modules: [
    '@nuxtjs/tailwindcss',
  ],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },
  // Optimizaciones de rendimiento
  app: {
    head: {
      htmlAttrs: {
        lang: 'es'
      },
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      script: [
        // Agregamos un script para manejar globalmente los errores de WebSocket
        { 
          innerHTML: `
            window.addEventListener('error', function(e) {
              if (e && e.message && (e.message.includes('WebSocket') || e.message.includes('ws://') || e.message.includes('24678') || e.message.includes('24680'))) {
                console.log('[Interceptado] Error WebSocket/HMR:', e.message);
                e.preventDefault();
                e.stopPropagation();
                return true;
              }
            }, {capture: true});
            
            // Interceptar errores de promesas no capturadas relacionadas con WebSocket
            window.addEventListener('unhandledrejection', function(e) {
              if (e && e.reason && e.reason.message && (e.reason.message.includes('WebSocket') || e.reason.message.includes('closed without opened'))) {
                console.log('[Interceptado] Promise rejection WebSocket:', e.reason.message);
                e.preventDefault();
                return true;
              }
            });
          `,
          type: 'text/javascript'
        }
      ]
    },
  },
  // Configuración del servidor de desarrollo
  devServer: {
    port: 3002,
    host: 'localhost',
  },
  
  // Variables de entorno para desarrollo
  runtimeConfig: {
    public: {
      supabaseUrl: process.env.SUPABASE_URL || '',
      supabaseKey: process.env.SUPABASE_KEY || '',
      // Configuración para HMR
      hmrEnabled: process.env.NODE_ENV === 'development' ? true : false,
    }
  },
  // Optimizaciones de build
  nitro: {
    prerender: {
      crawlLinks: false
    },
    minify: true,
    // Configuración para evitar problemas de permisos en Windows
    output: {
      dir: './.output',
      serverDir: './.output/server',
      publicDir: './.output/public'
    },
    // Evitar eliminar directorios antes de compilar
    storage: {
      fs: {
        driver: 'fs',
        base: './.data/storage'
      }
    }
  },
  // Optimizaciones de Vite
  vite: {
    server: {
      hmr: {
        protocol: 'ws',
        host: 'localhost',
        port: 24680, // Cambiar puerto HMR para evitar conflictos
        clientPort: 24680,
        timeout: 10000, // Aumentar timeout
      },
      fs: {
        strict: false // Reduce restricciones de acceso a archivos
      },
      watch: {
        usePolling: true, // Mejor compatibilidad en sistemas Windows
        interval: 1000
      }
    },
    build: {
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: process.env.NODE_ENV === 'production',
        }
      }
    },
    optimizeDeps: {
      include: ['vue', '@supabase/supabase-js']
    }
  },
  experimental: {
    renderJsonPayloads: true,
    viewTransition: true,
  }
})
