// Diagnóstico de Supabase para aicasino2
// Este script verifica la conexión con Supabase y la estructura de la tabla

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

// Cargar variables de entorno
dotenv.config();

const SUPABASE_URL = process.env.SUPABASE_URL || '';
const SUPABASE_KEY = process.env.SUPABASE_KEY || '';

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('Error: No se encontraron las credenciales de Supabase.');
  console.error('Asegúrate de tener un archivo .env con SUPABASE_URL y SUPABASE_KEY.');
  process.exit(1);
}

// Crear cliente de Supabase
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Función principal de diagnóstico
async function diagnoseSupabase() {
  console.log('=== Diagnóstico de Supabase ===');
  console.log(`URL: ${SUPABASE_URL}`);
  
  try {
    // 1. Verificar conexión
    console.log('\n1. Verificando conexión con Supabase...');
    const { data: tablesData, error: tablesError } = await supabase.rpc('get_tables');
    
    if (tablesError) {
      console.error('❌ Error al conectar con Supabase:', tablesError);
      return;
    }
    
    console.log('✅ Conexión establecida correctamente');
    console.log(`Tablas disponibles: ${tablesData.length}`);
    tablesData.forEach(table => console.log(` - ${table.table_name}`));
    
    // 2. Verificar tabla roulette_numbers_individual
    console.log('\n2. Verificando tabla roulette_numbers_individual...');
    const { data: columnData, error: columnError } = await supabase
      .from('roulette_numbers_individual')
      .select('*')
      .limit(1);
    
    if (columnError) {
      if (columnError.code === '42P01') {
        console.error('❌ La tabla roulette_numbers_individual no existe');
        await createTable();
      } else {
        console.error('❌ Error al consultar la tabla:', columnError);
      }
      return;
    }
    
    // La tabla existe, verificar columnas
    if (columnData.length > 0) {
      const columns = Object.keys(columnData[0]);
      console.log('✅ Tabla encontrada con las siguientes columnas:');
      columns.forEach(col => console.log(` - ${col}`));
      
      // Verificar si existe timestamp o created_at
      const hasTimestamp = columns.includes('timestamp');
      const hasCreatedAt = columns.includes('created_at');
      
      if (!hasTimestamp && !hasCreatedAt) {
        console.error('❌ No se encontró columna de fecha (timestamp o created_at)');
        await addDateColumn();
      } else {
        console.log(`✅ Columna de fecha encontrada: ${hasTimestamp ? 'timestamp' : 'created_at'}`);
      }
    } else {
      console.log('ℹ️ La tabla existe pero está vacía');
    }
    
    // 3. Verificar datos
    console.log('\n3. Verificando datos en la tabla...');
    let orderColumn = 'created_at';
    
    // Intentar con created_at primero
    let { data: recentData, error: recentError } = await supabase
      .from('roulette_numbers_individual')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(5);
    
    // Si falla, intentar con timestamp
    if (recentError && recentError.code === '42703') {
      console.log('ℹ️ created_at no existe, intentando con timestamp');
      orderColumn = 'timestamp';
      
      const result = await supabase
        .from('roulette_numbers_individual')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(5);
      
      recentData = result.data;
      recentError = result.error;
    }
    
    if (recentError) {
      console.error('❌ Error al obtener datos recientes:', recentError);
      return;
    }
    
    if (recentData && recentData.length > 0) {
      console.log(`✅ Se encontraron ${recentData.length} registros recientes`);
      console.log('Ejemplo de registro:');
      console.log(recentData[0]);
    } else {
      console.log('ℹ️ No hay datos en la tabla');
    }
    
    // Indicar qué cambios hacer en el código
    console.log('\n=== Recomendaciones ===');
    console.log(`Usa "${orderColumn}" como nombre de la columna de fecha en el código.`);
    
  } catch (error) {
    console.error('Error inesperado:', error);
  }
}

// Crear tabla si no existe
async function createTable() {
  console.log('Intentando crear la tabla roulette_numbers_individual...');
  
  // Usar SQL directo para crear la tabla
  const { error } = await supabase.rpc('execute_sql', { 
    sql: `
      CREATE TABLE roulette_numbers_individual (
        id SERIAL PRIMARY KEY,
        number INTEGER NOT NULL,
        color TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
    `
  });
  
  if (error) {
    console.error('❌ Error al crear la tabla:', error);
    return false;
  }
  
  console.log('✅ Tabla creada correctamente');
  return true;
}

// Añadir columna de fecha si no existe
async function addDateColumn() {
  console.log('Intentando añadir columna created_at...');
  
  // Usar SQL directo para añadir la columna
  const { error } = await supabase.rpc('execute_sql', { 
    sql: `
      ALTER TABLE roulette_numbers_individual 
      ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    `
  });
  
  if (error) {
    console.error('❌ Error al añadir columna:', error);
    return false;
  }
  
  console.log('✅ Columna created_at añadida correctamente');
  return true;
}

// Ejecutar diagnóstico
diagnoseSupabase().then(() => {
  console.log('\n=== Diagnóstico completado ===');
  process.exit(0);
}).catch(err => {
  console.error('Error fatal:', err);
  process.exit(1);
}); 