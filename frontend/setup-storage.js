import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// Obtener __dirname en ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Obtener la ruta absoluta del directorio de almacenamiento
const storageDir = resolve(__dirname, '.data', 'storage');

try {
  // Verificar si el directorio existe
  try {
    await fs.stat(storageDir);
    console.log(`ℹ️ Directorio de almacenamiento ya existe: ${storageDir}`);
  } catch (error) {
    // Si hay error es porque el directorio no existe
    if (error.code === 'ENOENT') {
      // Crear el directorio y sus padres de forma recursiva
      await fs.mkdir(storageDir, { recursive: true });
      console.log(`✅ Directorio de almacenamiento creado: ${storageDir}`);
    } else {
      throw error; // Otro tipo de error
    }
  }
} catch (error) {
  console.error(`❌ Error al configurar el directorio de almacenamiento: ${error.message}`);
  process.exit(1);
} 