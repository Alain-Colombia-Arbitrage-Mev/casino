-- Essential tables for the roulette application

-- Tabla principal de historial
CREATE TABLE IF NOT EXISTS roulette_history (
    id SERIAL PRIMARY KEY,
    numbers_string TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('UTC'::TEXT, NOW())
);

-- Tabla para números individuales
CREATE TABLE IF NOT EXISTS roulette_numbers_individual (
    id SERIAL PRIMARY KEY,
    history_entry_id INTEGER NOT NULL REFERENCES roulette_history(id) ON DELETE CASCADE,
    number_value INTEGER NOT NULL CHECK (number_value >= 0 AND number_value <= 36),
    color TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('UTC'::TEXT, NOW())
);

-- Tabla para el estado del analizador
CREATE TABLE IF NOT EXISTS analyzer_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    aciertos_individual INTEGER DEFAULT 0,
    aciertos_grupo INTEGER DEFAULT 0,
    aciertos_vecinos_0_10 INTEGER DEFAULT 0,
    aciertos_vecinos_7_27 INTEGER DEFAULT 0,
    total_predicciones_evaluadas INTEGER DEFAULT 0,
    aciertos_tia_lu INTEGER DEFAULT 0,
    tia_lu_estado_activa BOOLEAN DEFAULT FALSE,
    tia_lu_estado_giros_jugados INTEGER DEFAULT 0,
    tia_lu_estado_activada_con_33 BOOLEAN DEFAULT FALSE,
    tia_lu_estado_contador_desencadenantes_consecutivos INTEGER DEFAULT 0,
    tia_lu_estado_ultimo_numero_fue_desencadenante BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('UTC'::TEXT, NOW())
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_roulette_history_created_at ON roulette_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_roulette_numbers_history_id ON roulette_numbers_individual(history_entry_id);
CREATE INDEX IF NOT EXISTS idx_roulette_numbers_value ON roulette_numbers_individual(number_value);
CREATE INDEX IF NOT EXISTS idx_roulette_numbers_created_at ON roulette_numbers_individual(created_at DESC);

-- Insertar estado inicial del analizador si no existe
INSERT INTO analyzer_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING;