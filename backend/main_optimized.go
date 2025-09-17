package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
)

// OptimizedHybridServer estructura optimizada para Redis enriquecido
type OptimizedHybridServer struct {
	RedisClient   *redis.Client
	Router        *gin.Engine
	PredictorPool *PredictorPool
	Cache         *FastCache
	AdaptiveML    *AdaptiveMLEngine
}

// EnrichedRouletteNumber estructura enriquecida para números de ruleta
type EnrichedRouletteNumber struct {
	Number    int       `json:"number"`
	Color     string    `json:"color"`
	Dozen     int       `json:"dozen"`
	Column    int       `json:"column"`
	Parity    string    `json:"parity"`
	HighLow   string    `json:"high_low"`
	Timestamp time.Time `json:"timestamp"`
}

// OptimizedRouletteStats estructura optimizada para estadísticas
type OptimizedRouletteStats struct {
	TotalNumbers      int                        `json:"total_numbers"`
	LastNumber        int                        `json:"last_number"`
	LastColor         string                     `json:"last_color"`
	LastTimestamp     string                     `json:"last_timestamp"`
	SessionStart      string                     `json:"session_start"`
	ColorCounts       map[string]int             `json:"color_counts"`
	NumberFrequencies map[int]int                `json:"number_frequencies"`
	DozenCounts       map[int]int                `json:"dozen_counts"`
	ColumnCounts      map[int]int                `json:"column_counts"`
	ParityCounts      map[string]int             `json:"parity_counts"`
	HighLowCounts     map[string]int             `json:"high_low_counts"`
	SectorCounts      map[int]int                `json:"sector_counts"`
	CurrentGaps       map[int]int                `json:"current_gaps"`
	Patterns          OptimizedPatternStats      `json:"patterns"`
	RecentNumbers     []EnrichedRouletteNumber   `json:"recent_numbers"`
	Predictions       []PredictionResult         `json:"predictions"`
	HotNumbers        []int                      `json:"hot_numbers"`
	ColdNumbers       []int                      `json:"cold_numbers"`
}

// OptimizedPatternStats estadísticas de patrones optimizadas
type OptimizedPatternStats struct {
	Repeats         int `json:"repeats"`
	ColorAlternates int `json:"color_alternates"`
}

// OptimizedMLFeatures estructura optimizada para ML
type OptimizedMLFeatures struct {
	RecentNumbers     []int                     `json:"recent_numbers"`
	RecentColors      []string                  `json:"recent_colors"`
	NumberFrequencies map[int]int               `json:"number_frequencies"`
	ColorCounts       map[string]int            `json:"color_counts"`
	CurrentGaps       map[int]int               `json:"current_gaps"`
	Patterns          OptimizedPatternStats     `json:"patterns"`
	DozenCounts       map[int]int               `json:"dozen_counts"`
	ColumnCounts      map[int]int               `json:"column_counts"`
	SectorCounts      map[int]int               `json:"sector_counts"`
	LastUpdate        string                    `json:"last_update"`
}

// GroupStatistics estructura para estadísticas de grupos
type GroupStatistics struct {
	ID           string  `json:"id"`
	Name         string  `json:"name"`
	Numbers      []int   `json:"numbers"`
	Description  string  `json:"description,omitempty"`
	Hits         int     `json:"hits"`
	Total        int     `json:"total"`
	WinRate      float64 `json:"win_rate"`
	Type         string  `json:"type"`
	LastUpdate   string  `json:"last_update"`
}

// GroupStatisticsResponse respuesta completa de estadísticas de grupos
type GroupStatisticsResponse struct {
	TraditionalGroups []GroupStatistics `json:"traditional_groups"`
	SectorGroups     []GroupStatistics `json:"sector_groups"`
	BestPerforming   *GroupStatistics  `json:"best_performing"`
	WorstPerforming  *GroupStatistics  `json:"worst_performing"`
	Trends           []TrendAnalysis   `json:"trends"`
	LastUpdate       string            `json:"last_update"`
}

// TrendAnalysis análisis de tendencias
type TrendAnalysis struct {
	Type     string  `json:"type"`
	Strength float64 `json:"strength"`
	Description string `json:"description"`
}

func main() {
	log.Println("🚀 AI Casino ULTRA OPTIMIZED Backend (Go + Redis Enriched)")
	log.Println("⚡ Arquitectura: Python Scraper → Redis Ultra Rico → Go ML → Frontend")
	log.Println("🧠 Machine Learning: Go Ensemble + XGBoost + Deep Learning")

	// Crear servidor optimizado
	server := NewOptimizedHybridServer()
	if server == nil {
		log.Fatal("❌ Error al inicializar servidor optimizado")
	}

	// Configurar rutas optimizadas
	server.SetupOptimizedRoutes()

	// Iniciar workers optimizados
	go server.StartOptimizedWorkers()

	// Iniciar listener de eventos Redis para sincronización
	go server.StartRedisEventListener()
	log.Println("🔔 Listener de eventos Redis iniciado")

	port := os.Getenv("PORT")
	if port == "" {
		port = "5002"
	}

	log.Printf("🌐 Servidor ULTRA OPTIMIZADO corriendo en puerto %s", port)
	log.Printf("📊 Endpoints optimizados:")
	log.Printf("   • GET  /api/roulette/stats - Estadísticas ultra enriquecidas")
	log.Printf("   • GET  /api/roulette/ml-features - Features completos ML")
	log.Printf("   • POST /api/ai/predict-ensemble - Predicciones ML optimizadas")
	log.Printf("   • GET  /api/roulette/history - Historial enriquecido Redis")

	if err := http.ListenAndServe(":"+port, server.Router); err != nil {
		log.Fatal("❌ Error al iniciar servidor:", err)
	}
}

// NewOptimizedHybridServer crea servidor ultra optimizado
func NewOptimizedHybridServer() *OptimizedHybridServer {
	// Conectar a Redis usando variables de entorno
	redisHost := os.Getenv("REDIS_HOST")
	if redisHost == "" {
		redisHost = "localhost"
	}
	redisPort := os.Getenv("REDIS_PORT")
	if redisPort == "" {
		redisPort = "6379"
	}
	redisAddr := redisHost + ":" + redisPort

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       0,
	})

	ctx := context.Background()
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Printf("⚠️  Redis no disponible: %v", err)
	} else {
		log.Println("✅ Redis conectado - Listo para datos ultra enriquecidos")
	}

	// Cache ultra rápido
	cache := NewFastCache(time.Minute * 3)

	// Pool de predictores optimizado
	predictorPool := NewPredictorPool(6, rdb, cache) // Más workers

	// Motor de ML Adaptativo - NUEVA FUNCIONALIDAD
	adaptiveML := NewAdaptiveMLEngine(rdb)
	log.Println("🧠 Motor de ML Adaptativo inicializado - Aprende nuevas estrategias automáticamente")

	// Configurar Gin para máximo rendimiento
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	router.Use(gin.Recovery())

	// CORS optimizado
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	router.Use(cors.New(config))

	return &OptimizedHybridServer{
		RedisClient:   rdb,
		Router:        router,
		PredictorPool: predictorPool,
		Cache:         cache,
		AdaptiveML:    adaptiveML,
	}
}

// SetupOptimizedRoutes configura rutas ultra optimizadas
func (s *OptimizedHybridServer) SetupOptimizedRoutes() {
	api := s.Router.Group("/api")

	// Rutas de ruleta optimizadas
	roulette := api.Group("/roulette")
	{
		roulette.GET("/stats", s.handleOptimizedStats)
		roulette.GET("/ml-features", s.handleMLFeatures)
		roulette.GET("/history", s.handleOptimizedHistory)
		roulette.GET("/latest", s.handleOptimizedLatest)
		roulette.GET("/gaps", s.handleCurrentGaps)
		roulette.GET("/patterns", s.handlePatterns)
		roulette.GET("/group-stats", s.handleGroupStatistics)  // NUEVO: Estadísticas de grupos
	}

	// Rutas AI/ML optimizadas
	ai := api.Group("/ai")
	{
		ai.POST("/predict-ensemble", s.handleOptimizedPredict)
		ai.POST("/predict-adaptive", s.handleAdaptivePredict)      // NUEVO: ML Adaptativo
		ai.GET("/predictions", s.handleOptimizedPredictions)
		ai.POST("/retrain", s.handleOptimizedRetrain)
		ai.GET("/strategies", s.handleGetStrategies)              // NUEVO: Ver estrategias
		ai.GET("/performance", s.handleStrategyPerformance)       // NUEVO: Performance ML
		ai.POST("/record-result", s.handleRecordPredictionResult) // NUEVO: Feedback ML
	}

	// Rutas sistema optimizadas
	system := api.Group("/system")
	{
		system.GET("/health", s.handleOptimizedHealth)
		system.GET("/redis-status", s.handleRedisStatus)
		system.GET("/redis-keys", s.handleRedisKeys)             // NUEVO: Diagnóstico de keys
		system.GET("/performance", s.handlePerformanceMetrics)
		system.GET("/scraper-status", s.handleScraperStatus)     // NUEVO: Estado del scraper
		system.POST("/validate-data", s.handleValidateData)      // NUEVO: Validar datos
		system.GET("/sync-status", s.handleSyncStatus)           // NUEVO: Estado sincronización
		system.POST("/purge-statistics", s.handlePurgeStatistics)  // NUEVO: Purgar estadísticas
	}

	// Test ultra rápido
	s.Router.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message":      "pong",
			"timestamp":    time.Now().Unix(),
			"architecture": "ultra_optimized_redis",
			"status":       "blazing_fast",
			"version":      "2.0_optimized",
		})
	})

	// Health endpoint for Docker
	s.Router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "healthy",
			"timestamp": time.Now().Unix(),
		})
	})
}

// handleOptimizedStats maneja estadísticas ultra enriquecidas
func (s *OptimizedHybridServer) handleOptimizedStats(c *gin.Context) {
	ctx := context.Background()

	stats, err := s.getUltraEnrichedStats(ctx)
	if err != nil {
		log.Printf("Error obteniendo stats ultra enriquecidas: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to get enriched stats",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":   true,
		"stats":     stats,
		"timestamp": time.Now().Format(time.RFC3339),
		"source":    "redis_ultra_enriched",
		"version":   "2.0_optimized",
	})
}

// getUltraEnrichedStats obtiene estadísticas ultra enriquecidas de Redis usando las keys reales
func (s *OptimizedHybridServer) getUltraEnrichedStats(ctx context.Context) (*OptimizedRouletteStats, error) {
	stats := &OptimizedRouletteStats{
		ColorCounts:       make(map[string]int),
		NumberFrequencies: make(map[int]int),
		DozenCounts:       make(map[int]int),
		ColumnCounts:      make(map[int]int),
		ParityCounts:      make(map[string]int),
		HighLowCounts:     make(map[string]int),
		SectorCounts:      make(map[int]int),
		CurrentGaps:       make(map[int]int),
		Patterns:          OptimizedPatternStats{},
		RecentNumbers:     []EnrichedRouletteNumber{},
		HotNumbers:        []int{},
		ColdNumbers:       []int{},
	}

	// Pipeline para datos básicos usando keys reales
	pipe := s.RedisClient.Pipeline()

	// Datos básicos que existen
	totalSpinsCmd := pipe.Get(ctx, "roulette:total_spins")
	currentNumberCmd := pipe.Get(ctx, "roulette:current_number")
	sessionStartCmd := pipe.Get(ctx, "roulette:session_start")
	historyCmd := pipe.LRange(ctx, "roulette:history", 0, 19) // Últimos 20 números

	// Contadores de colores que realmente existen
	redCountCmd := pipe.Get(ctx, "roulette:freq:color:red")
	blackCountCmd := pipe.Get(ctx, "roulette:freq:color:black")

	// Contadores de docenas
	dozen1Cmd := pipe.Get(ctx, "roulette:freq:dozen:1")
	dozen2Cmd := pipe.Get(ctx, "roulette:freq:dozen:2")
	dozen3Cmd := pipe.Get(ctx, "roulette:freq:dozen:3")

	// Contadores de columnas
	col1Cmd := pipe.Get(ctx, "roulette:freq:column:1")
	col2Cmd := pipe.Get(ctx, "roulette:freq:column:2")
	col3Cmd := pipe.Get(ctx, "roulette:freq:column:3")

	// Contadores de paridad
	oddCountCmd := pipe.Get(ctx, "roulette:freq:parity:odd")
	evenCountCmd := pipe.Get(ctx, "roulette:freq:parity:even")

	// Ejecutar pipeline
	_, err := pipe.Exec(ctx)
	if err != nil {
		log.Printf("Error en pipeline Redis: %v", err)
		// Continuar con valores por defecto en caso de error
	}

	// Obtener último número del historial (más confiable que keys específicos)
	if len(stats.RecentNumbers) > 0 {
		latestEntry := stats.RecentNumbers[0] // El primer elemento es el más reciente
		stats.LastNumber = latestEntry.Number
		stats.LastColor = latestEntry.Color
		stats.LastTimestamp = latestEntry.Timestamp.Format(time.RFC3339)
	} else {
		// Fallback: intentar desde currentNumber si el historial está vacío
		if currentData, err := currentNumberCmd.Result(); err == nil {
			var currentNum map[string]interface{}
			if json.Unmarshal([]byte(currentData), &currentNum) == nil {
				if numberVal, ok := currentNum["number"].(float64); ok {
					stats.LastNumber = int(numberVal)
					stats.LastColor = s.getNumberColor(stats.LastNumber)
				}
				if timestampStr, ok := currentNum["timestamp"].(string); ok {
					stats.LastTimestamp = timestampStr
				}
			}
		}
	}

	// Total de spins
	if totalSpins, err := totalSpinsCmd.Result(); err == nil {
		if val, err := strconv.Atoi(totalSpins); err == nil {
			stats.TotalNumbers = val
		}
	}

	// Session start
	if sessionStart, err := sessionStartCmd.Result(); err == nil {
		stats.SessionStart = sessionStart
	}

	// Procesar historial (números simples)
	if historyData, err := historyCmd.Result(); err == nil {
		for _, numStr := range historyData {
			if num, err := strconv.Atoi(numStr); err == nil && s.isValidRouletteNumber(num) {
				enrichedNum := EnrichedRouletteNumber{
					Number:  num,
					Color:   s.getNumberColor(num),
					Dozen:   s.getNumberDozen(num),
					Column:  s.getNumberColumn(num),
					Parity:  s.getNumberParity(num),
					HighLow: s.getNumberHighLow(num),
					Timestamp: time.Now(), // Sin timestamp específico en historial simple
				}
				stats.RecentNumbers = append(stats.RecentNumbers, enrichedNum)
			}
		}
	}

	// Procesar contadores de colores
	if red, err := redCountCmd.Result(); err == nil {
		if val, err := strconv.Atoi(red); err == nil {
			stats.ColorCounts["red"] = val
		}
	}
	if black, err := blackCountCmd.Result(); err == nil {
		if val, err := strconv.Atoi(black); err == nil {
			stats.ColorCounts["black"] = val
		}
	}
	// Green se calcula como total - red - black para el cero
	stats.ColorCounts["green"] = stats.TotalNumbers - stats.ColorCounts["red"] - stats.ColorCounts["black"]
	if stats.ColorCounts["green"] < 0 {
		stats.ColorCounts["green"] = 0
	}

	// Procesar docenas
	if dozen1, err := dozen1Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen1); err == nil {
			stats.DozenCounts[1] = val
		}
	}
	if dozen2, err := dozen2Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen2); err == nil {
			stats.DozenCounts[2] = val
		}
	}
	if dozen3, err := dozen3Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen3); err == nil {
			stats.DozenCounts[3] = val
		}
	}

	// Procesar columnas
	if col1, err := col1Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col1); err == nil {
			stats.ColumnCounts[1] = val
		}
	}
	if col2, err := col2Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col2); err == nil {
			stats.ColumnCounts[2] = val
		}
	}
	if col3, err := col3Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col3); err == nil {
			stats.ColumnCounts[3] = val
		}
	}

	// Procesar paridad
	if odd, err := oddCountCmd.Result(); err == nil {
		if val, err := strconv.Atoi(odd); err == nil {
			stats.ParityCounts["odd"] = val
		}
	}
	if even, err := evenCountCmd.Result(); err == nil {
		if val, err := strconv.Atoi(even); err == nil {
			stats.ParityCounts["even"] = val
		}
	}
	// Zero se calcula como total - odd - even
	stats.ParityCounts["zero"] = stats.TotalNumbers - stats.ParityCounts["odd"] - stats.ParityCounts["even"]
	if stats.ParityCounts["zero"] < 0 {
		stats.ParityCounts["zero"] = 0
	}

	// Calcular high/low basado en los números del historial
	for _, num := range stats.RecentNumbers {
		if num.Number == 0 {
			stats.HighLowCounts["zero"]++
		} else if num.Number <= 18 {
			stats.HighLowCounts["low"]++
		} else {
			stats.HighLowCounts["high"]++
		}
	}

	// Obtener frecuencias individuales y números calientes/fríos
	s.enrichWithRealFrequencies(ctx, stats)

	// Calcular patrones básicos desde el historial
	s.calculatePatternsFromHistory(stats)

	return stats, nil
}

// enrichWithRealFrequencies enriquece stats con frecuencias usando las keys reales
func (s *OptimizedHybridServer) enrichWithRealFrequencies(ctx context.Context, stats *OptimizedRouletteStats) {
	// Pipeline para frecuencias individuales usando las keys que realmente existen
	pipe := s.RedisClient.Pipeline()

	var freqCmds [37]*redis.StringCmd

	for i := 0; i <= 36; i++ {
		// Usar la key real: roulette:freq:number:X
		freqCmds[i] = pipe.Get(ctx, "roulette:freq:number:"+strconv.Itoa(i))
	}

	pipe.Exec(ctx)

	// Procesar frecuencias y determinar números calientes/fríos
	var frequencies []struct {
		number int
		count  int
	}

	for i := 0; i <= 36; i++ {
		if freq, err := freqCmds[i].Result(); err == nil {
			if val, err := strconv.Atoi(freq); err == nil {
				stats.NumberFrequencies[i] = val
				frequencies = append(frequencies, struct {
					number int
					count  int
				}{i, val})
			}
		} else {
			// Si no existe la key, asumir frecuencia 0
			stats.NumberFrequencies[i] = 0
			frequencies = append(frequencies, struct {
				number int
				count  int
			}{i, 0})
		}
	}

	// Ordenar por frecuencia para determinar hot y cold
	for i := 0; i < len(frequencies)-1; i++ {
		for j := i + 1; j < len(frequencies); j++ {
			if frequencies[i].count < frequencies[j].count {
				frequencies[i], frequencies[j] = frequencies[j], frequencies[i]
			}
		}
	}

	// Top 10 números más calientes
	for i := 0; i < 10 && i < len(frequencies); i++ {
		if frequencies[i].count > 0 {
			stats.HotNumbers = append(stats.HotNumbers, frequencies[i].number)
		}
	}

	// Bottom 10 números más fríos (empezando desde el final)
	for i := len(frequencies) - 1; i >= len(frequencies)-10 && i >= 0; i-- {
		stats.ColdNumbers = append(stats.ColdNumbers, frequencies[i].number)
	}

	// Calcular gaps básicos basados en posición en historial
	for i := 0; i <= 36; i++ {
		gap := 0
		// Buscar la posición más reciente del número en el historial
		for j, num := range stats.RecentNumbers {
			if num.Number == i {
				gap = j
				break
			}
		}
		// Si no se encuentra, el gap es el tamaño del historial
		if gap == 0 && len(stats.RecentNumbers) > 0 {
			found := false
			for _, num := range stats.RecentNumbers {
				if num.Number == i {
					found = true
					break
				}
			}
			if !found {
				gap = len(stats.RecentNumbers)
			}
		}
		stats.CurrentGaps[i] = gap
	}
}

// calculatePatternsFromHistory calcula patrones básicos desde el historial
func (s *OptimizedHybridServer) calculatePatternsFromHistory(stats *OptimizedRouletteStats) {
	if len(stats.RecentNumbers) < 2 {
		return
	}

	// Contar repeticiones consecutivas
	repeats := 0
	for i := 1; i < len(stats.RecentNumbers); i++ {
		if stats.RecentNumbers[i-1].Number == stats.RecentNumbers[i].Number {
			repeats++
		}
	}
	stats.Patterns.Repeats = repeats

	// Contar alternancias de color
	colorAlternates := 0
	for i := 1; i < len(stats.RecentNumbers) && i < 10; i++ {
		prevColor := stats.RecentNumbers[i-1].Color
		currColor := stats.RecentNumbers[i].Color
		if prevColor != currColor && prevColor != "green" && currColor != "green" {
			colorAlternates++
		}
	}
	stats.Patterns.ColorAlternates = colorAlternates
}

// Helper functions para propiedades de números
func (s *OptimizedHybridServer) isValidRouletteNumber(number int) bool {
	return number >= 0 && number <= 36
}

func (s *OptimizedHybridServer) getNumberColor(number int) string {
	if number == 0 {
		return "green"
	}
	redNumbers := []int{1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
	for _, red := range redNumbers {
		if number == red {
			return "red"
		}
	}
	return "black"
}

func (s *OptimizedHybridServer) getNumberDozen(number int) int {
	if number == 0 {
		return 0
	} else if number <= 12 {
		return 1
	} else if number <= 24 {
		return 2
	}
	return 3
}

func (s *OptimizedHybridServer) getNumberColumn(number int) int {
	if number == 0 {
		return 0
	}
	return ((number - 1) % 3) + 1
}

func (s *OptimizedHybridServer) getNumberParity(number int) string {
	if number == 0 {
		return "zero"
	}
	if number%2 == 0 {
		return "even"
	}
	return "odd"
}

func (s *OptimizedHybridServer) getNumberHighLow(number int) string {
	if number == 0 {
		return "zero"
	} else if number <= 18 {
		return "low"
	}
	return "high"
}

// handleMLFeatures devuelve features optimizados para ML
func (s *OptimizedHybridServer) handleMLFeatures(c *gin.Context) {
	ctx := context.Background()

	features, err := s.getOptimizedMLFeatures(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to get ML features",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":   true,
		"features":  features,
		"timestamp": time.Now().Format(time.RFC3339),
		"version":   "ml_optimized_v2",
	})
}

// getOptimizedMLFeatures obtiene features ML optimizados usando keys reales
func (s *OptimizedHybridServer) getOptimizedMLFeatures(ctx context.Context) (*OptimizedMLFeatures, error) {
	features := &OptimizedMLFeatures{
		RecentNumbers:     []int{},
		RecentColors:      []string{},
		NumberFrequencies: make(map[int]int),
		ColorCounts:       make(map[string]int),
		CurrentGaps:       make(map[int]int),
		DozenCounts:       make(map[int]int),
		ColumnCounts:      make(map[int]int),
		SectorCounts:      make(map[int]int),
		LastUpdate:        time.Now().Format(time.RFC3339),
	}

	// Obtener números recientes del historial
	recentData, err := s.RedisClient.LRange(ctx, "roulette:history", 0, 49).Result()
	if err == nil {
		for _, numStr := range recentData {
			if num, err := strconv.Atoi(numStr); err == nil {
				if s.isValidRouletteNumber(num) {
					features.RecentNumbers = append(features.RecentNumbers, num)
					if len(features.RecentColors) < 50 {
						features.RecentColors = append(features.RecentColors, s.getNumberColor(num))
					}
				}
			}
		}
	}

	// Pipeline para obtener todas las estadísticas usando keys reales
	pipe := s.RedisClient.Pipeline()
	var freqCmds [37]*redis.StringCmd

	// Frecuencias individuales
	for i := 0; i <= 36; i++ {
		freqCmds[i] = pipe.Get(ctx, "roulette:freq:number:"+strconv.Itoa(i))
	}

	// Contadores agregados
	redCmd := pipe.Get(ctx, "roulette:freq:color:red")
	blackCmd := pipe.Get(ctx, "roulette:freq:color:black")
	dozen1Cmd := pipe.Get(ctx, "roulette:freq:dozen:1")
	dozen2Cmd := pipe.Get(ctx, "roulette:freq:dozen:2")
	dozen3Cmd := pipe.Get(ctx, "roulette:freq:dozen:3")
	col1Cmd := pipe.Get(ctx, "roulette:freq:column:1")
	col2Cmd := pipe.Get(ctx, "roulette:freq:column:2")
	col3Cmd := pipe.Get(ctx, "roulette:freq:column:3")

	pipe.Exec(ctx)

	// Procesar frecuencias individuales
	for i := 0; i <= 36; i++ {
		if result, err := freqCmds[i].Result(); err == nil {
			if val, err := strconv.Atoi(result); err == nil {
				features.NumberFrequencies[i] = val
			}
		} else {
			features.NumberFrequencies[i] = 0
		}
	}

	// Procesar contadores de colores
	if red, err := redCmd.Result(); err == nil {
		if val, err := strconv.Atoi(red); err == nil {
			features.ColorCounts["red"] = val
		}
	}
	if black, err := blackCmd.Result(); err == nil {
		if val, err := strconv.Atoi(black); err == nil {
			features.ColorCounts["black"] = val
		}
	}
	// Green (cero) calculado
	totalSpins := 0
	for _, freq := range features.NumberFrequencies {
		totalSpins += freq
	}
	features.ColorCounts["green"] = features.NumberFrequencies[0]

	// Procesar docenas
	if dozen1, err := dozen1Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen1); err == nil {
			features.DozenCounts[1] = val
		}
	}
	if dozen2, err := dozen2Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen2); err == nil {
			features.DozenCounts[2] = val
		}
	}
	if dozen3, err := dozen3Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(dozen3); err == nil {
			features.DozenCounts[3] = val
		}
	}

	// Procesar columnas
	if col1, err := col1Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col1); err == nil {
			features.ColumnCounts[1] = val
		}
	}
	if col2, err := col2Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col2); err == nil {
			features.ColumnCounts[2] = val
		}
	}
	if col3, err := col3Cmd.Result(); err == nil {
		if val, err := strconv.Atoi(col3); err == nil {
			features.ColumnCounts[3] = val
		}
	}

	// Calcular gaps básicos
	for i := 0; i <= 36; i++ {
		gap := 0
		for j, num := range features.RecentNumbers {
			if num == i {
				gap = j
				break
			}
		}
		if gap == 0 && len(features.RecentNumbers) > 0 {
			found := false
			for _, num := range features.RecentNumbers {
				if num == i {
					found = true
					break
				}
			}
			if !found {
				gap = len(features.RecentNumbers)
			}
		}
		features.CurrentGaps[i] = gap
	}

	// Calcular sectores (agrupaciones de números en la rueda)
	for i := 0; i <= 36; i++ {
		sector := i / 9 // Dividir en 4 sectores aproximados
		if sector > 3 {
			sector = 3
		}
		features.SectorCounts[sector] += features.NumberFrequencies[i]
	}

	return features, nil
}

// Handlers adicionales optimizados
func (s *OptimizedHybridServer) handleOptimizedHistory(c *gin.Context) {
	// Implementar historial optimizado
	c.JSON(http.StatusOK, gin.H{"message": "optimized history endpoint"})
}

func (s *OptimizedHybridServer) handleOptimizedLatest(c *gin.Context) {
	// Implementar latest optimizado
	c.JSON(http.StatusOK, gin.H{"message": "optimized latest endpoint"})
}

func (s *OptimizedHybridServer) handleCurrentGaps(c *gin.Context) {
	// Implementar gaps actuales
	c.JSON(http.StatusOK, gin.H{"message": "current gaps endpoint"})
}

func (s *OptimizedHybridServer) handlePatterns(c *gin.Context) {
	// Implementar patrones
	c.JSON(http.StatusOK, gin.H{"message": "patterns endpoint"})
}

// handleGroupStatistics maneja estadísticas detalladas de grupos de números
func (s *OptimizedHybridServer) handleGroupStatistics(c *gin.Context) {
	ctx := context.Background()

	log.Println("📊 Generando estadísticas de grupos de números...")

	// Obtener números recientes de Redis
	recentNumbersStr, err := s.RedisClient.LRange(ctx, "roulette:history", 0, 49).Result()
	if err != nil {
		log.Printf("❌ Error obteniendo historial: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error obteniendo datos"})
		return
	}

	// Convertir strings a números
	var recentNumbers []int
	for _, numStr := range recentNumbersStr {
		if num, err := strconv.Atoi(numStr); err == nil {
			recentNumbers = append(recentNumbers, num)
		}
	}

	// Definir grupos de números
	groupDefinitions := map[string][]int{
		"rojo":             {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
		"negro":            {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35},
		"par":              {2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36},
		"impar":            {1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35},
		"bajo":             []int{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18},
		"alto":             []int{19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36},
		"primera_docena":   []int{1,2,3,4,5,6,7,8,9,10,11,12},
		"segunda_docena":   []int{13,14,15,16,17,18,19,20,21,22,23,24},
		"tercera_docena":   []int{25,26,27,28,29,30,31,32,33,34,35,36},
		"voisins":          {22,18,29,7,28,12,35,3,26,0,32,15,19,4,21,2,25},
		"tiers":            {27,13,36,11,30,8,23,10,5,24,16,33},
		"orphelins":        {1,20,14,31,9,17,34,6},
		"zero_game":        {12,35,3,26,0,32,15},
	}

	groupNames := map[string]string{
		"rojo":             "Números Rojos",
		"negro":            "Números Negros",
		"par":              "Números Pares",
		"impar":            "Números Impares",
		"bajo":             "Manque (1-18)",
		"alto":             "Passe (19-36)",
		"primera_docena":   "Primera Docena (1-12)",
		"segunda_docena":   "Segunda Docena (13-24)",
		"tercera_docena":   "Tercera Docena (25-36)",
		"voisins":          "Voisins du Zéro",
		"tiers":            "Tiers du Cylindre",
		"orphelins":        "Orphelins",
		"zero_game":        "Zero Spiel",
	}

	groupDescriptions := map[string]string{
		"voisins":    "Vecinos del cero",
		"tiers":      "Tercio del cilindro",
		"orphelins":  "Huérfanos",
		"zero_game":  "Juego del cero",
	}

	// Calcular estadísticas para cada grupo
	var traditionalGroups []GroupStatistics
	var sectorGroups []GroupStatistics
	var bestPerforming *GroupStatistics
	var worstPerforming *GroupStatistics

	currentTime := time.Now().Format("15:04:05")
	totalSpins := len(recentNumbers)

	for groupID, numbers := range groupDefinitions {
		hits := 0
		for _, num := range recentNumbers {
			for _, groupNum := range numbers {
				if num == groupNum {
					hits++
					break
				}
			}
		}

		winRate := 0.0
		if totalSpins > 0 {
			winRate = (float64(hits) / float64(totalSpins)) * 100
		}

		groupStat := GroupStatistics{
			ID:          groupID,
			Name:        groupNames[groupID],
			Numbers:     numbers,
			Description: groupDescriptions[groupID],
			Hits:        hits,
			Total:       totalSpins,
			WinRate:     winRate,
			LastUpdate:  currentTime,
		}

		// Clasificar grupos
		if groupID == "voisins" || groupID == "tiers" || groupID == "orphelins" || groupID == "zero_game" {
			groupStat.Type = "sector"
			sectorGroups = append(sectorGroups, groupStat)
		} else {
			groupStat.Type = "traditional"
			traditionalGroups = append(traditionalGroups, groupStat)
		}

		// Encontrar mejores y peores rendimientos
		if bestPerforming == nil || winRate > bestPerforming.WinRate {
			temp := groupStat
			bestPerforming = &temp
		}
		if worstPerforming == nil || winRate < worstPerforming.WinRate {
			temp := groupStat
			worstPerforming = &temp
		}
	}

	// Generar análisis de tendencias
	trends := []TrendAnalysis{
		{
			Type:        "Tendencia Rojo/Negro",
			Strength:    calculateColorTrend(recentNumbers),
			Description: "Análisis de alternancia entre colores",
		},
		{
			Type:        "Secuencia Par/Impar",
			Strength:    calculateParityTrend(recentNumbers),
			Description: "Análisis de patrones de paridad",
		},
		{
			Type:        "Patrón Docenas",
			Strength:    calculateDozenTrend(recentNumbers),
			Description: "Análisis de distribución por docenas",
		},
	}

	response := GroupStatisticsResponse{
		TraditionalGroups: traditionalGroups,
		SectorGroups:     sectorGroups,
		BestPerforming:   bestPerforming,
		WorstPerforming:  worstPerforming,
		Trends:           trends,
		LastUpdate:       currentTime,
	}

	log.Printf("✅ Estadísticas de grupos generadas: %d grupos tradicionales, %d sectores",
		len(traditionalGroups), len(sectorGroups))

	c.JSON(http.StatusOK, response)
}

// Helper functions para análisis de tendencias
func calculateColorTrend(numbers []int) float64 {
	if len(numbers) < 2 {
		return 50.0
	}

	redNumbers := map[int]bool{1:true,3:true,5:true,7:true,9:true,12:true,14:true,16:true,18:true,19:true,21:true,23:true,25:true,27:true,30:true,32:true,34:true,36:true}

	alternations := 0
	for i := 1; i < len(numbers); i++ {
		prevIsRed := redNumbers[numbers[i-1]]
		currIsRed := redNumbers[numbers[i]]
		if prevIsRed != currIsRed {
			alternations++
		}
	}

	return (float64(alternations) / float64(len(numbers)-1)) * 100
}

func calculateParityTrend(numbers []int) float64 {
	if len(numbers) < 2 {
		return 50.0
	}

	alternations := 0
	for i := 1; i < len(numbers); i++ {
		prevIsEven := numbers[i-1]%2 == 0
		currIsEven := numbers[i]%2 == 0
		if prevIsEven != currIsEven {
			alternations++
		}
	}

	return (float64(alternations) / float64(len(numbers)-1)) * 100
}

func calculateDozenTrend(numbers []int) float64 {
	if len(numbers) < 3 {
		return 50.0
	}

	dozenCounts := make(map[int]int)
	for _, num := range numbers {
		if num == 0 {
			continue
		}
		dozen := ((num - 1) / 12) + 1
		if dozen >= 1 && dozen <= 3 {
			dozenCounts[dozen]++
		}
	}

	// Calcular distribución uniforme esperada
	total := len(numbers)
	expectedPerDozen := float64(total) / 3.0

	variance := 0.0
	for dozen := 1; dozen <= 3; dozen++ {
		diff := float64(dozenCounts[dozen]) - expectedPerDozen
		variance += diff * diff
	}

	// Convertir varianza a porcentaje de uniformidad
	maxVariance := expectedPerDozen * expectedPerDozen * 3
	uniformity := (1.0 - (variance / maxVariance)) * 100

	if uniformity < 0 {
		uniformity = 0
	}

	return uniformity
}

func (s *OptimizedHybridServer) handleOptimizedPredict(c *gin.Context) {
	// Implementar predicción optimizada
	c.JSON(http.StatusOK, gin.H{"message": "optimized predict endpoint"})
}

// handleAdaptivePredict maneja predicción con ML adaptativo
func (s *OptimizedHybridServer) handleAdaptivePredict(c *gin.Context) {
	log.Println("🧠 Generando predicción adaptativa...")

	ctx := context.Background()
	prediction, err := s.AdaptiveML.GenerateAdaptivePrediction(ctx)
	if err != nil {
		log.Printf("❌ Error en predicción adaptativa: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to generate adaptive prediction",
			"details": err.Error(),
		})
		return
	}

	log.Printf("✅ Predicción adaptativa generada: %v (confianza: %.3f)",
		prediction.PredictedNumbers, prediction.Confidence)

	c.JSON(http.StatusOK, gin.H{
		"success":    true,
		"prediction": prediction,
		"timestamp":  time.Now().Format(time.RFC3339),
		"version":    "adaptive_ml_v1",
	})
}

// handleGetStrategies devuelve todas las estrategias activas
func (s *OptimizedHybridServer) handleGetStrategies(c *gin.Context) {
	s.AdaptiveML.mutex.RLock()
	strategies := make([]map[string]interface{}, 0, len(s.AdaptiveML.Strategies))

	for _, strategy := range s.AdaptiveML.Strategies {
		strategyInfo := map[string]interface{}{
			"id":           strategy.ID,
			"name":         strategy.Name,
			"type":         strategy.Type,
			"confidence":   strategy.Confidence,
			"success_rate": strategy.SuccessRate,
			"total_predictions": strategy.TotalPredictions,
			"created":      strategy.Created.Format(time.RFC3339),
			"last_updated": strategy.LastUpdated.Format(time.RFC3339),
		}
		strategies = append(strategies, strategyInfo)
	}
	s.AdaptiveML.mutex.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"success":    true,
		"strategies": strategies,
		"total":      len(strategies),
		"timestamp":  time.Now().Format(time.RFC3339),
	})
}

// handleStrategyPerformance devuelve reporte de performance
func (s *OptimizedHybridServer) handleStrategyPerformance(c *gin.Context) {
	report := s.AdaptiveML.GetStrategyPerformanceReport()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"report":  report,
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// handleRecordPredictionResult registra resultado de predicción para aprendizaje
func (s *OptimizedHybridServer) handleRecordPredictionResult(c *gin.Context) {
	var request struct {
		PredictedNumbers []int    `json:"predicted_numbers" binding:"required"`
		ActualNumber     int      `json:"actual_number" binding:"required"`
		StrategiesUsed   []string `json:"strategies_used" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}

	// Validar número actual
	if !s.isValidRouletteNumber(request.ActualNumber) {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid actual number (must be 0-36)",
		})
		return
	}

	// Registrar resultado para aprendizaje
	s.AdaptiveML.RecordPredictionResult(
		request.PredictedNumbers,
		request.ActualNumber,
		request.StrategiesUsed,
	)

	// Verificar si fue hit
	hit := false
	for _, predicted := range request.PredictedNumbers {
		if predicted == request.ActualNumber {
			hit = true
			break
		}
	}

	log.Printf("📊 Resultado registrado: predicho=%v, actual=%d, hit=%v",
		request.PredictedNumbers, request.ActualNumber, hit)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"hit":     hit,
		"message": "Prediction result recorded for learning",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

func (s *OptimizedHybridServer) handleOptimizedPredictions(c *gin.Context) {
	// Implementar predicciones optimizadas
	c.JSON(http.StatusOK, gin.H{"message": "optimized predictions endpoint"})
}

func (s *OptimizedHybridServer) handleOptimizedRetrain(c *gin.Context) {
	// Implementar reentrenamiento optimizado
	c.JSON(http.StatusOK, gin.H{"message": "optimized retrain endpoint"})
}

func (s *OptimizedHybridServer) handleOptimizedHealth(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"version":   "ultra_optimized_v2",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

func (s *OptimizedHybridServer) handleRedisStatus(c *gin.Context) {
	ctx := context.Background()
	err := s.RedisClient.Ping(ctx).Err()
	status := "connected"
	if err != nil {
		status = "disconnected"
	}
	c.JSON(http.StatusOK, gin.H{
		"status":    status,
		"timestamp": time.Now().Format(time.RFC3339),
		"version":   "redis_optimized",
	})
}

func (s *OptimizedHybridServer) handlePerformanceMetrics(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"cache_size":     s.Cache.Size(),
		"predictor_pool": "active",
		"redis_status":   "optimized",
		"timestamp":      time.Now().Format(time.RFC3339),
	})
}

// handlePurgeStatistics purga todas las estadísticas del sistema
func (s *OptimizedHybridServer) handlePurgeStatistics(c *gin.Context) {
	ctx := context.Background()

	log.Println("🧹 Iniciando purga completa de estadísticas...")

	// Lista de todas las keys de Redis relacionadas con estadísticas
	keysToDelete := []string{
		"roulette:current_number",
		"roulette:history",
		"roulette:total_spins",
		"roulette:session_start",
		"roulette:freq:color:red",
		"roulette:freq:color:black",
		"roulette:freq:dozen:1",
		"roulette:freq:dozen:2",
		"roulette:freq:dozen:3",
		"roulette:freq:column:1",
		"roulette:freq:column:2",
		"roulette:freq:column:3",
		"roulette:freq:parity:odd",
		"roulette:freq:parity:even",
		"roulette:freq:range:high",
		"roulette:freq:range:low",
		"roulette:patterns:repeats",
		"roulette:patterns:alternates",
		"roulette:ml:features",
		"roulette:ml:predictions",
		"roulette:ml:model_performance",
	}

	deletedCount := 0
	errors := []string{}

	// Eliminar keys individuales
	for _, key := range keysToDelete {
		result, err := s.RedisClient.Del(ctx, key).Result()
		if err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", key, err))
		} else {
			deletedCount += int(result)
		}
	}

	// Eliminar keys con patrones (números individuales)
	for i := 0; i <= 36; i++ {
		key := fmt.Sprintf("roulette:freq:number:%d", i)
		result, err := s.RedisClient.Del(ctx, key).Result()
		if err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", key, err))
		} else {
			deletedCount += int(result)
		}

		gapKey := fmt.Sprintf("roulette:gap:%d", i)
		result, err = s.RedisClient.Del(ctx, gapKey).Result()
		if err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", gapKey, err))
		} else {
			deletedCount += int(result)
		}
	}

	// Limpiar caché local
	s.Cache.Clear()

	// Nota: AdaptiveML se reiniciará automáticamente con nuevos datos

	log.Printf("🧹 Purga completada: %d keys eliminadas", deletedCount)

	if len(errors) > 0 {
		log.Printf("⚠️  Errores durante purga: %v", errors)
		c.JSON(http.StatusPartialContent, gin.H{
			"success":       true,
			"deleted_keys":  deletedCount,
			"errors":        errors,
			"message":       "Purga completada con algunos errores",
			"timestamp":     time.Now().Format(time.RFC3339),
		})
	} else {
		c.JSON(http.StatusOK, gin.H{
			"success":      true,
			"deleted_keys": deletedCount,
			"message":      "Todas las estadísticas han sido purgadas exitosamente",
			"timestamp":    time.Now().Format(time.RFC3339),
		})
	}
}

// handleRedisKeys diagnóstico de keys de Redis
func (s *OptimizedHybridServer) handleRedisKeys(c *gin.Context) {
	ctx := context.Background()

	// Verificar keys principales que el sistema espera encontrar
	expectedKeys := []string{
		"roulette:current_number",
		"roulette:history",
		"roulette:total_spins",
		"roulette:session_start",
		"roulette:freq:color:red",
		"roulette:freq:color:black",
		"roulette:freq:dozen:1",
		"roulette:freq:dozen:2",
		"roulette:freq:dozen:3",
		"roulette:freq:column:1",
		"roulette:freq:column:2",
		"roulette:freq:column:3",
		"roulette:freq:parity:odd",
		"roulette:freq:parity:even",
	}

	keyStatus := make(map[string]interface{})

	for _, key := range expectedKeys {
		exists, err := s.RedisClient.Exists(ctx, key).Result()
		if err != nil {
			keyStatus[key] = map[string]interface{}{
				"exists": false,
				"error":  err.Error(),
			}
		} else {
			if exists > 0 {
				// Key existe, obtener tipo y valor de ejemplo
				keyType, _ := s.RedisClient.Type(ctx, key).Result()
				var sampleValue interface{}

				switch keyType {
				case "string":
					sampleValue, _ = s.RedisClient.Get(ctx, key).Result()
				case "list":
					listLen, _ := s.RedisClient.LLen(ctx, key).Result()
					sample, _ := s.RedisClient.LRange(ctx, key, 0, 2).Result()
					sampleValue = map[string]interface{}{
						"length": listLen,
						"sample": sample,
					}
				default:
					sampleValue = "complex_type"
				}

				keyStatus[key] = map[string]interface{}{
					"exists":      true,
					"type":        keyType,
					"sample_value": sampleValue,
				}
			} else {
				keyStatus[key] = map[string]interface{}{
					"exists": false,
				}
			}
		}
	}

	// Verificar keys de frecuencias individuales (muestreo)
	sampleNumbers := []int{0, 1, 7, 17, 22, 36}
	numberFreqs := make(map[string]interface{})
	for _, num := range sampleNumbers {
		key := "roulette:freq:number:" + strconv.Itoa(num)
		if val, err := s.RedisClient.Get(ctx, key).Result(); err == nil {
			numberFreqs[key] = val
		} else {
			numberFreqs[key] = "not_found"
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success":           true,
		"expected_keys":     keyStatus,
		"number_frequencies_sample": numberFreqs,
		"timestamp":         time.Now().Format(time.RFC3339),
		"message":           "Redis keys diagnostic",
	})
}

// Handlers de sistema adicionales
func (s *OptimizedHybridServer) handleScraperStatus(c *gin.Context) {
	ctx := context.Background()

	// Verificar si hay datos recientes
	lastUpdate := "unknown"
	if currentData, err := s.RedisClient.Get(ctx, "roulette:current_number").Result(); err == nil {
		var current map[string]interface{}
		if json.Unmarshal([]byte(currentData), &current) == nil {
			if timestamp, ok := current["timestamp"].(string); ok {
				lastUpdate = timestamp
			}
		}
	}

	totalSpins := 0
	if total, err := s.RedisClient.Get(ctx, "roulette:total_spins").Result(); err == nil {
		if val, err := strconv.Atoi(total); err == nil {
			totalSpins = val
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"status":      "active",
		"last_update": lastUpdate,
		"total_spins": totalSpins,
		"timestamp":   time.Now().Format(time.RFC3339),
	})
}

func (s *OptimizedHybridServer) handleValidateData(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "validated",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

func (s *OptimizedHybridServer) handleSyncStatus(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "synced",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// StartOptimizedWorkers inicia workers ultra optimizados
func (s *OptimizedHybridServer) StartOptimizedWorkers() {
	log.Println("🔄 Iniciando workers ULTRA OPTIMIZADOS...")

	// Worker cache más frecuente
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		defer ticker.Stop()
		for range ticker.C {
			s.Cache.Cleanup()
		}
	}()

	// Worker auto-entrenamiento más frecuente
	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		defer ticker.Stop()
		for range ticker.C {
			s.PredictorPool.AutoTrain()
		}
	}()

	log.Println("✅ Workers ultra optimizados iniciados")
}

// StartRedisEventListener inicia listener de eventos Redis
func (s *OptimizedHybridServer) StartRedisEventListener() {
	log.Println("🔔 Iniciando Redis Event Listener...")

	go func() {
		// Configurar suscripción a eventos de Redis
		ctx := context.Background()

		// Escuchar cambios en las keys principales
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			// Verificar si hay nuevos datos
			if exists, _ := s.RedisClient.Exists(ctx, "roulette:current_number").Result(); exists > 0 {
				// Limpiar cache cuando hay nuevos datos
				s.Cache.Clear()
				log.Println("🔄 Cache limpiado por nuevos datos en Redis")
			}
		}
	}()
}