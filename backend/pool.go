package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
)

// PredictionTask representa una tarea de predicción
type PredictionTask struct {
	History        []int
	PredictionType string
	ResponseChan   chan *PredictionResult
	ErrorChan      chan error
}

// PredictorWorker representa un worker de predicción
type PredictorWorker struct {
	ID        int
	Predictor *RoulettePredictor
	TaskChan  <-chan *PredictionTask
	QuitChan  <-chan struct{}
}

// NewPredictorWorker crea un nuevo worker
func NewPredictorWorker(id int, taskChan <-chan *PredictionTask, quitChan <-chan struct{}) *PredictorWorker {
	return &PredictorWorker{
		ID:        id,
		Predictor: NewRoulettePredictor(),
		TaskChan:  taskChan,
		QuitChan:  quitChan,
	}
}

// Start inicia el worker
func (w *PredictorWorker) Start() {
	go func() {
		for {
			select {
			case task := <-w.TaskChan:
				w.processTask(task)
			case <-w.QuitChan:
				log.Printf("🔄 Worker %d terminando...", w.ID)
				return
			}
		}
	}()
}

// processTask procesa una tarea de predicción
func (w *PredictorWorker) processTask(task *PredictionTask) {
	startTime := time.Now()

	result, err := w.Predictor.PredictEnsemble(task.History, task.PredictionType)

	duration := time.Since(startTime)

	if err != nil {
		log.Printf("⚠️  Worker %d: Error en predicción (%.2fms): %v", w.ID, float64(duration.Nanoseconds())/1e6, err)
		task.ErrorChan <- err
		return
	}

	log.Printf("✅ Worker %d: Predicción completada en %.2fms", w.ID, float64(duration.Nanoseconds())/1e6)
	task.ResponseChan <- result
}

// PredictorPool maneja un pool de workers de predicción
type PredictorPool struct {
	WorkerCount   int
	TaskQueue     chan *PredictionTask
	QuitChannel   chan struct{}
	Workers       []*PredictorWorker
	RedisClient   *redis.Client
	Cache         *FastCache
	mutex         sync.RWMutex
	isRunning     bool
	TaskCount     int64
	CompletedTasks int64
}

// NewPredictorPool crea un nuevo pool de predictores
func NewPredictorPool(workerCount int, redisClient *redis.Client, cache *FastCache) *PredictorPool {
	return &PredictorPool{
		WorkerCount: workerCount,
		TaskQueue:   make(chan *PredictionTask, workerCount*2), // Buffer para mejor rendimiento
		QuitChannel: make(chan struct{}),
		Workers:     make([]*PredictorWorker, workerCount),
		RedisClient: redisClient,
		Cache:       cache,
	}
}

// Start inicia el pool de workers
func (p *PredictorPool) Start() {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if p.isRunning {
		return
	}

	log.Printf("🚀 Iniciando pool de predictores con %d workers...", p.WorkerCount)

	// Crear y iniciar workers
	for i := 0; i < p.WorkerCount; i++ {
		worker := NewPredictorWorker(i+1, p.TaskQueue, p.QuitChannel)
		p.Workers[i] = worker
		worker.Start()
		log.Printf("⚡ Worker %d iniciado", i+1)
	}

	p.isRunning = true
	log.Println("✅ Pool de predictores completamente iniciado")
}

// Stop detiene el pool de workers
func (p *PredictorPool) Stop() {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if !p.isRunning {
		return
	}

	log.Println("🛑 Deteniendo pool de predictores...")

	close(p.QuitChannel)
	p.isRunning = false

	log.Println("✅ Pool de predictores detenido")
}

// SubmitPrediction envía una tarea de predicción al pool
func (p *PredictorPool) SubmitPrediction(history []int, predictionType string) (*PredictionResult, error) {
	// Verificar si el pool está corriendo
	p.mutex.RLock()
	if !p.isRunning {
		p.mutex.RUnlock()
		p.Start() // Auto-start si no está corriendo
		p.mutex.RLock()
	}
	p.mutex.RUnlock()

	// Crear canales para la respuesta
	responseChan := make(chan *PredictionResult, 1)
	errorChan := make(chan error, 1)

	// Crear tarea
	task := &PredictionTask{
		History:        history,
		PredictionType: predictionType,
		ResponseChan:   responseChan,
		ErrorChan:      errorChan,
	}

	// Enviar tarea al pool con timeout
	select {
	case p.TaskQueue <- task:
		p.TaskCount++
	case <-time.After(time.Second * 2):
		return nil, fmt.Errorf("timeout: pool saturado")
	}

	// Esperar resultado con timeout
	select {
	case result := <-responseChan:
		p.CompletedTasks++
		return result, nil
	case err := <-errorChan:
		return nil, err
	case <-time.After(time.Second * 10): // Timeout de 10 segundos
		return nil, fmt.Errorf("timeout: predicción tardó más de 10 segundos")
	}
}

// GetStats obtiene estadísticas del pool
func (p *PredictorPool) GetStats() map[string]interface{} {
	p.mutex.RLock()
	defer p.mutex.RUnlock()

	stats := map[string]interface{}{
		"worker_count":     p.WorkerCount,
		"is_running":       p.isRunning,
		"tasks_submitted":  p.TaskCount,
		"tasks_completed":  p.CompletedTasks,
		"queue_length":     len(p.TaskQueue),
		"success_rate":     0.0,
	}

	if p.TaskCount > 0 {
		stats["success_rate"] = float64(p.CompletedTasks) / float64(p.TaskCount) * 100
	}

	return stats
}

// AutoTrain ejecuta auto-entrenamiento en background
func (p *PredictorPool) AutoTrain() {
	log.Println("🤖 Iniciando auto-entrenamiento...")

	// Obtener datos históricos de Redis
	ctx := context.Background()
	history, err := p.getHistoryFromRedis(ctx, 100)
	if err != nil {
		log.Printf("⚠️  Error obteniendo historial para entrenamiento: %v", err)
		return
	}

	if len(history) < 50 {
		log.Printf("⚠️  Datos insuficientes para entrenamiento: %d números", len(history))
		return
	}

	// Simular entrenamiento (en una implementación real, aquí iría el entrenamiento de ML)
	go func() {
		time.Sleep(time.Second * 2) // Simular tiempo de entrenamiento
		log.Printf("✅ Auto-entrenamiento completado con %d datos", len(history))

		// Limpiar cache después del entrenamiento
		for _, worker := range p.Workers {
			if worker.Predictor != nil {
				worker.Predictor.PredictionCache.Clear()
				worker.Predictor.FeatureCache.Clear()
			}
		}
		log.Println("🧹 Cache de predictores limpiado después del entrenamiento")
	}()
}

// getHistoryFromRedis obtiene historial de números de Redis
func (p *PredictorPool) getHistoryFromRedis(ctx context.Context, limit int) ([]int, error) {
	// Obtener historial de Redis
	historyStrings, err := p.RedisClient.LRange(ctx, "roulette:history", 0, int64(limit-1)).Result()
	if err != nil {
		return nil, err
	}

	history := make([]int, len(historyStrings))
	for i, str := range historyStrings {
		if num, parseErr := parseInt(str); parseErr == nil {
			history[i] = num
		}
	}

	return history, nil
}

// parseInt convierte string a int de manera segura
func parseInt(s string) (int, error) {
	// Implementación simple de conversión
	num := 0
	for _, char := range s {
		if char >= '0' && char <= '9' {
			num = num*10 + int(char-'0')
		} else {
			return 0, fmt.Errorf("invalid character: %c", char)
		}
	}
	return num, nil
}

// HealthCheck verifica la salud del pool
func (p *PredictorPool) HealthCheck() map[string]interface{} {
	stats := p.GetStats()

	health := map[string]interface{}{
		"status":       "healthy",
		"stats":        stats,
		"cache_size":   p.Cache.Size(),
		"timestamp":    time.Now().Format(time.RFC3339),
	}

	// Verificar si hay problemas
	if !p.isRunning {
		health["status"] = "stopped"
	} else if len(p.TaskQueue) >= p.WorkerCount*2 {
		health["status"] = "overloaded"
	} else if p.TaskCount > 0 && float64(p.CompletedTasks)/float64(p.TaskCount) < 0.9 {
		health["status"] = "degraded"
	}

	return health
}