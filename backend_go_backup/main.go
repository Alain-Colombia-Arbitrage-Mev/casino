package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
)

// CasinoServer estructura principal del servidor
type CasinoServer struct {
	RedisClient    *redis.Client
	PredictorPool  *PredictorPool
	Cache          *FastCache
	Router         *gin.Engine
}

func main() {
	log.Println("🚀 Iniciando AI Casino Backend en Go...")
	log.Println("⚡ Multithreading: ACTIVADO")
	log.Println("🧠 Machine Learning: ACTIVADO")
	log.Println("📈 Auto-training: ACTIVADO")

	// Crear servidor
	server := NewCasinoServer()
	if server == nil {
		log.Fatal("❌ Error al inicializar servidor")
	}

	// Configurar rutas
	server.SetupRoutes()

	// Iniciar workers en background
	go server.StartBackgroundWorkers()

	// Obtener puerto
	port := os.Getenv("PORT")
	if port == "" {
		port = "5001"
	}

	log.Printf("🌐 Servidor corriendo en puerto %s", port)
	log.Printf("📊 Endpoints disponibles:")
	log.Printf("   • POST /api/ai/predict-ensemble")
	log.Printf("   • POST /api/ai/auto-retrain")
	log.Printf("   • GET  /api/ai/strategy-performance")
	log.Printf("   • POST /api/ml/train-xgboost")
	log.Printf("   • POST /api/roulette/numbers")

	// Iniciar servidor HTTP
	if err := http.ListenAndServe(":"+port, server.Router); err != nil {
		log.Fatal("❌ Error al iniciar servidor:", err)
	}
}

// NewCasinoServer crea una nueva instancia del servidor
func NewCasinoServer() *CasinoServer {
	// Conectar a Redis
	rdb := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
	})

	// Crear cache rápido
	cache := NewFastCache(time.Minute * 5) // TTL de 5 minutos

	// Crear pool de predictores para multithreading
	predictorPool := NewPredictorPool(4, rdb, cache) // 4 workers concurrentes

	// Configurar Gin
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	router.Use(gin.Recovery())

	// Configurar CORS
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	router.Use(cors.New(config))

	return &CasinoServer{
		RedisClient:   rdb,
		PredictorPool: predictorPool,
		Cache:        cache,
		Router:       router,
	}
}

// StartBackgroundWorkers inicia workers en background para tareas asíncronas
func (s *CasinoServer) StartBackgroundWorkers() {
	log.Println("🔄 Iniciando workers en background...")

	// Worker para auto-entrenamiento
	go s.autoTrainingWorker()

	// Worker para limpieza de cache
	go s.cacheCleanupWorker()

	// Worker para métricas
	go s.metricsWorker()
}

// autoTrainingWorker maneja el auto-entrenamiento en background
func (s *CasinoServer) autoTrainingWorker() {
	ticker := time.NewTicker(10 * time.Minute) // Cada 10 minutos
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			log.Println("🤖 Ejecutando auto-entrenamiento...")
			s.PredictorPool.AutoTrain()
		}
	}
}

// cacheCleanupWorker limpia el cache periódicamente
func (s *CasinoServer) cacheCleanupWorker() {
	ticker := time.NewTicker(2 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.Cache.Cleanup()
		}
	}
}

// metricsWorker recolecta métricas del sistema
func (s *CasinoServer) metricsWorker() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// Recolectar y almacenar métricas
			s.collectMetrics()
		}
	}
}

// collectMetrics recolecta métricas del sistema
func (s *CasinoServer) collectMetrics() {
	// Implementar recolección de métricas
	// Esto será expandido más adelante
}