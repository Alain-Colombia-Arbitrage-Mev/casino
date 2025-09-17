package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
)

// AdaptiveMLEngine Motor de ML que aprende nuevas estrategias automáticamente
type AdaptiveMLEngine struct {
	RedisClient      *redis.Client
	Strategies       map[string]*Strategy
	PerformanceTrack map[string]*StrategyPerformance
	mutex            sync.RWMutex
	learningRate     float64
	adaptationPeriod time.Duration
	lastAdaptation   time.Time
}

// Strategy representa una estrategia aprendida
type Strategy struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Parameters      map[string]float64     `json:"parameters"`
	Conditions      []StrategyCondition    `json:"conditions"`
	Actions         []StrategyAction       `json:"actions"`
	Confidence      float64                `json:"confidence"`
	Created         time.Time              `json:"created"`
	LastUpdated     time.Time              `json:"last_updated"`
	SuccessRate     float64                `json:"success_rate"`
	TotalPredictions int                   `json:"total_predictions"`
}

// StrategyCondition condición para activar estrategia
type StrategyCondition struct {
	Field     string  `json:"field"`      // "gap", "frequency", "pattern", etc.
	Operator  string  `json:"operator"`   // ">", "<", "=", "contains"
	Value     float64 `json:"value"`
	Weight    float64 `json:"weight"`
}

// StrategyAction acción a tomar cuando se cumple condición
type StrategyAction struct {
	Type       string             `json:"type"`        // "predict", "boost", "avoid"
	Target     interface{}        `json:"target"`      // número(s) a predecir/evitar
	Confidence float64            `json:"confidence"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// StrategyPerformance métricas de rendimiento de estrategia
type StrategyPerformance struct {
	StrategyID       string            `json:"strategy_id"`
	TotalUses        int               `json:"total_uses"`
	SuccessfulHits   int               `json:"successful_hits"`
	SuccessRate      float64           `json:"success_rate"`
	AverageConfidence float64          `json:"average_confidence"`
	LastUsed         time.Time         `json:"last_used"`
	RecentPerformance []float64        `json:"recent_performance"` // últimas 20 predicciones
	TrendDirection   string            `json:"trend_direction"`   // "improving", "declining", "stable"
}

// AdaptivePrediction predicción adaptativa mejorada
type AdaptivePrediction struct {
	PredictedNumbers []int                     `json:"predicted_numbers"`
	Confidence       float64                   `json:"confidence"`
	StrategiesUsed   []string                  `json:"strategies_used"`
	Reasoning        []string                  `json:"reasoning"`
	RiskLevel        string                    `json:"risk_level"`
	AlternativeNumbers []int                   `json:"alternative_numbers"`
	Metadata         map[string]interface{}    `json:"metadata"`
	Timestamp        time.Time                 `json:"timestamp"`
}

// NewAdaptiveMLEngine crea un nuevo motor adaptativo
func NewAdaptiveMLEngine(redisClient *redis.Client) *AdaptiveMLEngine {
	engine := &AdaptiveMLEngine{
		RedisClient:      redisClient,
		Strategies:       make(map[string]*Strategy),
		PerformanceTrack: make(map[string]*StrategyPerformance),
		learningRate:     0.1,
		adaptationPeriod: time.Minute * 5,
		lastAdaptation:   time.Now(),
	}

	// Cargar estrategias existentes
	engine.loadStrategiesFromRedis()

	// Inicializar estrategias básicas si no existen
	if len(engine.Strategies) == 0 {
		engine.initializeBaseStrategies()
	}

	// Iniciar goroutine de adaptación continua
	go engine.continuousAdaptation()

	return engine
}

// initializeBaseStrategies inicializa estrategias base
func (aml *AdaptiveMLEngine) initializeBaseStrategies() {
	log.Println("🧠 Inicializando estrategias base de ML adaptativo...")

	strategies := []*Strategy{
		// Estrategia 1: Gap Analysis
		{
			ID:   "gap_hunter",
			Name: "Gap Hunter Strategy",
			Type: "gap_analysis",
			Parameters: map[string]float64{
				"min_gap":       15.0,
				"max_gap":       50.0,
				"gap_weight":    0.8,
				"freq_weight":   0.2,
			},
			Conditions: []StrategyCondition{
				{Field: "gap", Operator: ">", Value: 15.0, Weight: 0.8},
				{Field: "frequency", Operator: "<", Value: 0.02, Weight: 0.2},
			},
			Actions: []StrategyAction{
				{Type: "predict", Confidence: 0.7, Metadata: map[string]interface{}{"reason": "high_gap"}},
			},
			Confidence:       0.6,
			Created:          time.Now(),
			LastUpdated:      time.Now(),
			SuccessRate:      0.0,
			TotalPredictions: 0,
		},

		// Estrategia 2: Hot Numbers
		{
			ID:   "hot_streaks",
			Name: "Hot Numbers Strategy",
			Type: "frequency_analysis",
			Parameters: map[string]float64{
				"hot_threshold":    0.05,
				"streak_length":    3.0,
				"momentum_weight":  0.9,
			},
			Conditions: []StrategyCondition{
				{Field: "frequency", Operator: ">", Value: 0.05, Weight: 0.6},
				{Field: "recent_streak", Operator: ">=", Value: 2.0, Weight: 0.4},
			},
			Actions: []StrategyAction{
				{Type: "predict", Confidence: 0.65, Metadata: map[string]interface{}{"reason": "hot_streak"}},
			},
			Confidence:       0.55,
			Created:          time.Now(),
			LastUpdated:      time.Now(),
			SuccessRate:      0.0,
			TotalPredictions: 0,
		},

		// Estrategia 3: Pattern Recognition
		{
			ID:   "pattern_seeker",
			Name: "Pattern Recognition Strategy",
			Type: "pattern_analysis",
			Parameters: map[string]float64{
				"pattern_length":    5.0,
				"similarity_threshold": 0.8,
				"history_depth":     50.0,
			},
			Conditions: []StrategyCondition{
				{Field: "pattern_match", Operator: ">", Value: 0.7, Weight: 0.9},
			},
			Actions: []StrategyAction{
				{Type: "predict", Confidence: 0.8, Metadata: map[string]interface{}{"reason": "pattern_detected"}},
			},
			Confidence:       0.7,
			Created:          time.Now(),
			LastUpdated:      time.Now(),
			SuccessRate:      0.0,
			TotalPredictions: 0,
		},

		// Estrategia 4: Sector Analysis
		{
			ID:   "sector_momentum",
			Name: "Sector Momentum Strategy",
			Type: "spatial_analysis",
			Parameters: map[string]float64{
				"sector_heat":      0.15,
				"momentum_period":  10.0,
				"spatial_weight":   0.7,
			},
			Conditions: []StrategyCondition{
				{Field: "sector_frequency", Operator: ">", Value: 0.15, Weight: 0.8},
				{Field: "sector_momentum", Operator: ">", Value: 0.1, Weight: 0.2},
			},
			Actions: []StrategyAction{
				{Type: "predict", Confidence: 0.6, Metadata: map[string]interface{}{"reason": "sector_hot"}},
			},
			Confidence:       0.5,
			Created:          time.Now(),
			LastUpdated:      time.Now(),
			SuccessRate:      0.0,
			TotalPredictions: 0,
		},

		// Estrategia 5: Anti-Pattern (Contrarian)
		{
			ID:   "contrarian",
			Name: "Contrarian Strategy",
			Type: "contrarian_analysis",
			Parameters: map[string]float64{
				"cold_threshold":   0.01,
				"avoidance_period": 20.0,
				"contrarian_weight": 0.6,
			},
			Conditions: []StrategyCondition{
				{Field: "frequency", Operator: "<", Value: 0.01, Weight: 0.5},
				{Field: "gap", Operator: ">", Value: 30.0, Weight: 0.5},
			},
			Actions: []StrategyAction{
				{Type: "avoid", Confidence: 0.4, Metadata: map[string]interface{}{"reason": "too_cold"}},
			},
			Confidence:       0.4,
			Created:          time.Now(),
			LastUpdated:      time.Now(),
			SuccessRate:      0.0,
			TotalPredictions: 0,
		},
	}

	// Guardar estrategias
	aml.mutex.Lock()
	for _, strategy := range strategies {
		aml.Strategies[strategy.ID] = strategy
		aml.PerformanceTrack[strategy.ID] = &StrategyPerformance{
			StrategyID:        strategy.ID,
			TotalUses:         0,
			SuccessfulHits:    0,
			SuccessRate:       0.0,
			AverageConfidence: strategy.Confidence,
			LastUsed:          time.Now(),
			RecentPerformance: []float64{},
			TrendDirection:    "stable",
		}
	}
	aml.mutex.Unlock()

	// Guardar en Redis
	aml.saveStrategiesToRedis()
	log.Printf("✅ Inicializadas %d estrategias base", len(strategies))
}

// GenerateAdaptivePrediction genera predicción usando estrategias adaptativas
func (aml *AdaptiveMLEngine) GenerateAdaptivePrediction(ctx context.Context) (*AdaptivePrediction, error) {
	log.Println("🧠 Generando predicción adaptativa...")

	// Obtener datos actuales de Redis
	gameState, err := aml.getCurrentGameState(ctx)
	if err != nil {
		return nil, fmt.Errorf("error obteniendo estado del juego: %v", err)
	}

	// Evaluar cada estrategia
	strategyResults := make(map[string]*StrategyResult)

	aml.mutex.RLock()
	for strategyID, strategy := range aml.Strategies {
		result := aml.evaluateStrategy(strategy, gameState)
		if result.ShouldActivate {
			strategyResults[strategyID] = result
		}
	}
	aml.mutex.RUnlock()

	// Combinar resultados de estrategias activas
	prediction := aml.combineStrategyResults(strategyResults, gameState)

	// Actualizar métricas de uso
	aml.updateStrategyUsage(strategyResults)

	log.Printf("✅ Predicción generada usando %d estrategias", len(prediction.StrategiesUsed))
	return prediction, nil
}

// StrategyResult resultado de evaluación de estrategia
type StrategyResult struct {
	StrategyID      string
	ShouldActivate  bool
	Confidence      float64
	PredictedNumbers []int
	Reasoning       string
	Metadata        map[string]interface{}
}

// GameState estado actual del juego
type GameState struct {
	RecentNumbers     []int
	NumberFrequencies map[int]int
	CurrentGaps       map[int]int
	SectorCounts      map[int]int
	TotalSpins        int
	LastNumber        int
	Patterns          map[string]interface{}
	Timestamp         time.Time
}

// getCurrentGameState obtiene estado actual del juego desde Redis
func (aml *AdaptiveMLEngine) getCurrentGameState(ctx context.Context) (*GameState, error) {
	gameState := &GameState{
		NumberFrequencies: make(map[int]int),
		CurrentGaps:       make(map[int]int),
		SectorCounts:      make(map[int]int),
		Patterns:          make(map[string]interface{}),
		Timestamp:         time.Now(),
	}

	// Pipeline para obtener todos los datos necesarios
	pipe := aml.RedisClient.Pipeline()

	// Datos básicos
	totalSpinsCmd := pipe.Get(ctx, "roulette:total_spins")
	latestNumberCmd := pipe.Get(ctx, "roulette:latest")
	historyCmd := pipe.LRange(ctx, "roulette:history", 0, 49)

	// Frecuencias
	var freqCmds [37]*redis.StringCmd
	for i := 0; i <= 36; i++ {
		freqCmds[i] = pipe.Get(ctx, fmt.Sprintf("roulette:numbers:%d", i))
	}

	// Gaps
	var gapCmds [37]*redis.StringCmd
	for i := 0; i <= 36; i++ {
		gapCmds[i] = pipe.Get(ctx, fmt.Sprintf("roulette:gap:%d", i))
	}

	// Sectores
	var sectorCmds [9]*redis.StringCmd
	for i := 0; i < 9; i++ {
		sectorCmds[i] = pipe.Get(ctx, fmt.Sprintf("roulette:sectors:%d", i))
	}

	// Patrones
	repeatsCmd := pipe.Get(ctx, "roulette:patterns:repeat")
	alternatesCmd := pipe.Get(ctx, "roulette:patterns:color_alternate")

	// Ejecutar pipeline
	_, err := pipe.Exec(ctx)
	if err != nil {
		return nil, err
	}

	// Procesar resultados
	if totalSpins, err := totalSpinsCmd.Result(); err == nil {
		if val, err := strconv.Atoi(totalSpins); err == nil {
			gameState.TotalSpins = val
		}
	}

	if latestNumber, err := latestNumberCmd.Result(); err == nil {
		if val, err := strconv.Atoi(latestNumber); err == nil {
			gameState.LastNumber = val
		}
	}

	if history, err := historyCmd.Result(); err == nil {
		for _, numStr := range history {
			if num, err := strconv.Atoi(numStr); err == nil {
				gameState.RecentNumbers = append(gameState.RecentNumbers, num)
			}
		}
	}

	// Procesar frecuencias
	for i := 0; i <= 36; i++ {
		if freq, err := freqCmds[i].Result(); err == nil {
			if val, err := strconv.Atoi(freq); err == nil {
				gameState.NumberFrequencies[i] = val
			}
		}
	}

	// Procesar gaps
	for i := 0; i <= 36; i++ {
		if gap, err := gapCmds[i].Result(); err == nil {
			if val, err := strconv.Atoi(gap); err == nil {
				gameState.CurrentGaps[i] = val
			}
		}
	}

	// Procesar sectores
	for i := 0; i < 9; i++ {
		if sector, err := sectorCmds[i].Result(); err == nil {
			if val, err := strconv.Atoi(sector); err == nil {
				gameState.SectorCounts[i] = val
			}
		}
	}

	// Procesar patrones
	if repeats, err := repeatsCmd.Result(); err == nil {
		if val, err := strconv.Atoi(repeats); err == nil {
			gameState.Patterns["repeats"] = val
		}
	}

	if alternates, err := alternatesCmd.Result(); err == nil {
		if val, err := strconv.Atoi(alternates); err == nil {
			gameState.Patterns["color_alternates"] = val
		}
	}

	return gameState, nil
}

// evaluateStrategy evalúa si una estrategia debe activarse
func (aml *AdaptiveMLEngine) evaluateStrategy(strategy *Strategy, gameState *GameState) *StrategyResult {
	result := &StrategyResult{
		StrategyID:       strategy.ID,
		ShouldActivate:   false,
		Confidence:       0.0,
		PredictedNumbers: []int{},
		Reasoning:        "",
		Metadata:         make(map[string]interface{}),
	}

	totalScore := 0.0
	maxScore := 0.0

	// Evaluar cada condición
	for _, condition := range strategy.Conditions {
		conditionMet, score := aml.evaluateCondition(condition, gameState, strategy)
		totalScore += score * condition.Weight
		maxScore += condition.Weight

		if conditionMet {
			result.Reasoning += fmt.Sprintf("%s %s %.2f; ", condition.Field, condition.Operator, condition.Value)
		}
	}

	// Calcular confianza normalizada
	if maxScore > 0 {
		normalizedScore := totalScore / maxScore
		result.Confidence = normalizedScore * strategy.Confidence

		// Activar si supera umbral
		if normalizedScore > 0.6 {
			result.ShouldActivate = true
			result.PredictedNumbers = aml.generatePredictionsForStrategy(strategy, gameState)
		}
	}

	return result
}

// evaluateCondition evalúa una condición específica
func (aml *AdaptiveMLEngine) evaluateCondition(condition StrategyCondition, gameState *GameState, strategy *Strategy) (bool, float64) {
	switch condition.Field {
	case "gap":
		return aml.evaluateGapCondition(condition, gameState)
	case "frequency":
		return aml.evaluateFrequencyCondition(condition, gameState)
	case "pattern_match":
		return aml.evaluatePatternCondition(condition, gameState)
	case "sector_frequency":
		return aml.evaluateSectorCondition(condition, gameState)
	case "recent_streak":
		return aml.evaluateStreakCondition(condition, gameState)
	default:
		return false, 0.0
	}
}

// evaluateGapCondition evalúa condiciones de gap
func (aml *AdaptiveMLEngine) evaluateGapCondition(condition StrategyCondition, gameState *GameState) (bool, float64) {
	maxGap := 0
	for _, gap := range gameState.CurrentGaps {
		if gap > maxGap {
			maxGap = gap
		}
	}

	switch condition.Operator {
	case ">":
		if float64(maxGap) > condition.Value {
			return true, math.Min(float64(maxGap)/condition.Value, 2.0) // Cap at 2x
		}
	case "<":
		if float64(maxGap) < condition.Value {
			return true, condition.Value/math.Max(float64(maxGap), 1.0)
		}
	}

	return false, 0.0
}

// evaluateFrequencyCondition evalúa condiciones de frecuencia
func (aml *AdaptiveMLEngine) evaluateFrequencyCondition(condition StrategyCondition, gameState *GameState) (bool, float64) {
	if gameState.TotalSpins == 0 {
		return false, 0.0
	}

	maxFreq := 0.0
	for _, freq := range gameState.NumberFrequencies {
		frequency := float64(freq) / float64(gameState.TotalSpins)
		if frequency > maxFreq {
			maxFreq = frequency
		}
	}

	switch condition.Operator {
	case ">":
		if maxFreq > condition.Value {
			return true, maxFreq / condition.Value
		}
	case "<":
		if maxFreq < condition.Value {
			return true, condition.Value / math.Max(maxFreq, 0.001)
		}
	}

	return false, 0.0
}

// evaluatePatternCondition evalúa condiciones de patrones
func (aml *AdaptiveMLEngine) evaluatePatternCondition(condition StrategyCondition, gameState *GameState) (bool, float64) {
	// Análisis de patrones en historial reciente
	if len(gameState.RecentNumbers) < 5 {
		return false, 0.0
	}

	// Buscar patrones repetitivos
	patternScore := aml.calculatePatternScore(gameState.RecentNumbers)

	if patternScore > condition.Value {
		return true, patternScore
	}

	return false, 0.0
}

// evaluateSectorCondition evalúa condiciones de sector
func (aml *AdaptiveMLEngine) evaluateSectorCondition(condition StrategyCondition, gameState *GameState) (bool, float64) {
	if gameState.TotalSpins == 0 {
		return false, 0.0
	}

	maxSectorFreq := 0.0
	for _, count := range gameState.SectorCounts {
		freq := float64(count) / float64(gameState.TotalSpins)
		if freq > maxSectorFreq {
			maxSectorFreq = freq
		}
	}

	if maxSectorFreq > condition.Value {
		return true, maxSectorFreq / condition.Value
	}

	return false, 0.0
}

// evaluateStreakCondition evalúa condiciones de racha
func (aml *AdaptiveMLEngine) evaluateStreakCondition(condition StrategyCondition, gameState *GameState) (bool, float64) {
	if len(gameState.RecentNumbers) < 3 {
		return false, 0.0
	}

	// Buscar rachas de números similares (mismo color, docena, etc.)
	maxStreak := aml.calculateMaxStreak(gameState.RecentNumbers)

	if float64(maxStreak) >= condition.Value {
		return true, float64(maxStreak) / condition.Value
	}

	return false, 0.0
}

// Helper functions
func (aml *AdaptiveMLEngine) calculatePatternScore(numbers []int) float64 {
	if len(numbers) < 5 {
		return 0.0
	}

	// Buscar secuencias repetitivas
	patternScore := 0.0

	// Analizar últimos 5 números
	recent5 := numbers[:5]

	// Buscar repeticiones
	for i := 0; i < len(recent5)-1; i++ {
		for j := i + 1; j < len(recent5); j++ {
			if recent5[i] == recent5[j] {
				patternScore += 0.2
			}
		}
	}

	// Analizar secuencias aritméticas
	for i := 0; i < len(recent5)-2; i++ {
		diff1 := recent5[i+1] - recent5[i]
		diff2 := recent5[i+2] - recent5[i+1]
		if diff1 == diff2 && diff1 != 0 {
			patternScore += 0.3
		}
	}

	return math.Min(patternScore, 1.0)
}

func (aml *AdaptiveMLEngine) calculateMaxStreak(numbers []int) int {
	if len(numbers) < 2 {
		return 0
	}

	maxStreak := 1
	currentStreak := 1

	for i := 1; i < len(numbers); i++ {
		// Definir "similar" (mismo color, misma docena, etc.)
		if aml.areNumbersSimilar(numbers[i-1], numbers[i]) {
			currentStreak++
			if currentStreak > maxStreak {
				maxStreak = currentStreak
			}
		} else {
			currentStreak = 1
		}
	}

	return maxStreak
}

func (aml *AdaptiveMLEngine) areNumbersSimilar(num1, num2 int) bool {
	// Mismo color
	if aml.getNumberColor(num1) == aml.getNumberColor(num2) {
		return true
	}

	// Misma docena
	if aml.getNumberDozen(num1) == aml.getNumberDozen(num2) {
		return true
	}

	return false
}

func (aml *AdaptiveMLEngine) getNumberColor(number int) string {
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

func (aml *AdaptiveMLEngine) getNumberDozen(number int) int {
	if number == 0 {
		return 0
	} else if number <= 12 {
		return 1
	} else if number <= 24 {
		return 2
	}
	return 3
}

// generatePredictionsForStrategy genera predicciones basadas en estrategia
func (aml *AdaptiveMLEngine) generatePredictionsForStrategy(strategy *Strategy, gameState *GameState) []int {
	predictions := []int{}

	switch strategy.Type {
	case "gap_analysis":
		predictions = aml.generateGapPredictions(strategy, gameState)
	case "frequency_analysis":
		predictions = aml.generateFrequencyPredictions(strategy, gameState)
	case "pattern_analysis":
		predictions = aml.generatePatternPredictions(strategy, gameState)
	case "spatial_analysis":
		predictions = aml.generateSpatialPredictions(strategy, gameState)
	case "contrarian_analysis":
		predictions = aml.generateContrarianPredictions(strategy, gameState)
	}

	return predictions
}

func (aml *AdaptiveMLEngine) generateGapPredictions(strategy *Strategy, gameState *GameState) []int {
	type numberGap struct {
		Number int
		Gap    int
	}

	var candidates []numberGap
	minGap := int(strategy.Parameters["min_gap"])
	maxGap := int(strategy.Parameters["max_gap"])

	for number, gap := range gameState.CurrentGaps {
		if gap >= minGap && gap <= maxGap {
			candidates = append(candidates, numberGap{Number: number, Gap: gap})
		}
	}

	// Ordenar por gap descendente
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].Gap > candidates[j].Gap
	})

	// Tomar top 3
	predictions := []int{}
	for i := 0; i < len(candidates) && i < 3; i++ {
		predictions = append(predictions, candidates[i].Number)
	}

	return predictions
}

func (aml *AdaptiveMLEngine) generateFrequencyPredictions(strategy *Strategy, gameState *GameState) []int {
	type numberFreq struct {
		Number    int
		Frequency float64
	}

	var candidates []numberFreq
	hotThreshold := strategy.Parameters["hot_threshold"]

	for number, freq := range gameState.NumberFrequencies {
		if gameState.TotalSpins > 0 {
			frequency := float64(freq) / float64(gameState.TotalSpins)
			if frequency > hotThreshold {
				candidates = append(candidates, numberFreq{Number: number, Frequency: frequency})
			}
		}
	}

	// Ordenar por frecuencia descendente
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].Frequency > candidates[j].Frequency
	})

	// Tomar top 3
	predictions := []int{}
	for i := 0; i < len(candidates) && i < 3; i++ {
		predictions = append(predictions, candidates[i].Number)
	}

	return predictions
}

func (aml *AdaptiveMLEngine) generatePatternPredictions(strategy *Strategy, gameState *GameState) []int {
	if len(gameState.RecentNumbers) < 5 {
		return []int{}
	}

	// Análisis de patrones en números recientes
	predictions := []int{}

	// Buscar números que siguen patrones detectados
	recent := gameState.RecentNumbers[:5]

	// Patrón: repetición del último número
	if len(recent) >= 2 && recent[0] == recent[1] {
		predictions = append(predictions, recent[0])
	}

	// Patrón: secuencia aritmética
	if len(recent) >= 3 {
		diff1 := recent[1] - recent[0]
		diff2 := recent[2] - recent[1]
		if diff1 == diff2 {
			nextInSeq := recent[0] + diff1*3
			if nextInSeq >= 0 && nextInSeq <= 36 {
				predictions = append(predictions, nextInSeq)
			}
		}
	}

	// Patrón: números en mismo sector
	if len(recent) >= 2 {
		lastSector := aml.getNumberSector(recent[0])
		for i := 0; i <= 36; i++ {
			if aml.getNumberSector(i) == lastSector && i != recent[0] {
				predictions = append(predictions, i)
				if len(predictions) >= 3 {
					break
				}
			}
		}
	}

	return predictions
}

func (aml *AdaptiveMLEngine) generateSpatialPredictions(strategy *Strategy, gameState *GameState) []int {
	// Encontrar sector más caliente
	hotSector := 0
	maxCount := 0
	for sector, count := range gameState.SectorCounts {
		if count > maxCount {
			maxCount = count
			hotSector = sector
		}
	}

	// Generar números del sector caliente
	predictions := []int{}
	for number := 0; number <= 36; number++ {
		if aml.getNumberSector(number) == hotSector {
			predictions = append(predictions, number)
			if len(predictions) >= 5 {
				break
			}
		}
	}

	return predictions
}

func (aml *AdaptiveMLEngine) generateContrarianPredictions(strategy *Strategy, gameState *GameState) []int {
	type numberFreq struct {
		Number    int
		Frequency float64
	}

	var candidates []numberFreq
	coldThreshold := strategy.Parameters["cold_threshold"]

	for number, freq := range gameState.NumberFrequencies {
		if gameState.TotalSpins > 0 {
			frequency := float64(freq) / float64(gameState.TotalSpins)
			if frequency < coldThreshold {
				candidates = append(candidates, numberFreq{Number: number, Frequency: frequency})
			}
		}
	}

	// Ordenar por frecuencia ascendente (más fríos primero)
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].Frequency < candidates[j].Frequency
	})

	// Tomar top 3 más fríos
	predictions := []int{}
	for i := 0; i < len(candidates) && i < 3; i++ {
		predictions = append(predictions, candidates[i].Number)
	}

	return predictions
}

func (aml *AdaptiveMLEngine) getNumberSector(number int) int {
	wheelOrder := []int{0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26}

	for i, num := range wheelOrder {
		if num == number {
			return i / 5 // 9 sectores (0-8)
		}
	}
	return 0
}

// combineStrategyResults combina resultados de múltiples estrategias
func (aml *AdaptiveMLEngine) combineStrategyResults(results map[string]*StrategyResult, gameState *GameState) *AdaptivePrediction {
	numberScores := make(map[int]float64)
	strategiesUsed := []string{}
	reasoning := []string{}
	totalConfidence := 0.0

	// Combinar predicciones de todas las estrategias activas
	for strategyID, result := range results {
		strategiesUsed = append(strategiesUsed, strategyID)
		reasoning = append(reasoning, result.Reasoning)
		totalConfidence += result.Confidence

		// Agregar score a cada número predicho
		for _, number := range result.PredictedNumbers {
			numberScores[number] += result.Confidence
		}
	}

	// Ordenar números por score
	type numberScore struct {
		Number int
		Score  float64
	}

	var sortedNumbers []numberScore
	for number, score := range numberScores {
		sortedNumbers = append(sortedNumbers, numberScore{Number: number, Score: score})
	}

	sort.Slice(sortedNumbers, func(i, j int) bool {
		return sortedNumbers[i].Score > sortedNumbers[j].Score
	})

	// Top predicciones
	finalPredictions := []int{}
	alternativeNumbers := []int{}

	for i, ns := range sortedNumbers {
		if i < 3 {
			finalPredictions = append(finalPredictions, ns.Number)
		} else if i < 6 {
			alternativeNumbers = append(alternativeNumbers, ns.Number)
		}
	}

	// Calcular confianza promedio
	avgConfidence := totalConfidence / float64(len(results))
	if avgConfidence > 1.0 {
		avgConfidence = 1.0
	}

	// Determinar nivel de riesgo
	riskLevel := "medium"
	if avgConfidence > 0.8 {
		riskLevel = "low"
	} else if avgConfidence < 0.4 {
		riskLevel = "high"
	}

	return &AdaptivePrediction{
		PredictedNumbers:   finalPredictions,
		Confidence:         avgConfidence,
		StrategiesUsed:     strategiesUsed,
		Reasoning:          reasoning,
		RiskLevel:          riskLevel,
		AlternativeNumbers: alternativeNumbers,
		Metadata: map[string]interface{}{
			"total_strategies": len(results),
			"game_state_timestamp": gameState.Timestamp,
			"total_spins": gameState.TotalSpins,
		},
		Timestamp: time.Now(),
	}
}

// updateStrategyUsage actualiza métricas de uso de estrategias
func (aml *AdaptiveMLEngine) updateStrategyUsage(results map[string]*StrategyResult) {
	aml.mutex.Lock()
	defer aml.mutex.Unlock()

	for strategyID := range results {
		if perf, exists := aml.PerformanceTrack[strategyID]; exists {
			perf.TotalUses++
			perf.LastUsed = time.Now()
		}
	}
}

// RecordPredictionResult registra el resultado de una predicción
func (aml *AdaptiveMLEngine) RecordPredictionResult(predictedNumbers []int, actualNumber int, strategiesUsed []string) {
	aml.mutex.Lock()
	defer aml.mutex.Unlock()

	hit := false
	for _, predicted := range predictedNumbers {
		if predicted == actualNumber {
			hit = true
			break
		}
	}

	// Actualizar performance de cada estrategia usada
	for _, strategyID := range strategiesUsed {
		if perf, exists := aml.PerformanceTrack[strategyID]; exists {
			if hit {
				perf.SuccessfulHits++
			}

			// Actualizar success rate
			if perf.TotalUses > 0 {
				perf.SuccessRate = float64(perf.SuccessfulHits) / float64(perf.TotalUses)
			}

			// Actualizar performance reciente
			hitValue := 0.0
			if hit {
				hitValue = 1.0
			}
			perf.RecentPerformance = append(perf.RecentPerformance, hitValue)

			// Mantener solo últimas 20 predicciones
			if len(perf.RecentPerformance) > 20 {
				perf.RecentPerformance = perf.RecentPerformance[1:]
			}

			// Calcular tendencia
			perf.TrendDirection = aml.calculateTrend(perf.RecentPerformance)

			// Actualizar confianza de la estrategia
			if strategy, exists := aml.Strategies[strategyID]; exists {
				strategy.SuccessRate = perf.SuccessRate
				strategy.TotalPredictions++
				strategy.LastUpdated = time.Now()

				// Adaptar parámetros basado en performance
				aml.adaptStrategyParameters(strategy, perf)
			}
		}
	}

	// Guardar métricas actualizadas
	aml.savePerformanceToRedis()
}

// calculateTrend calcula la tendencia de performance
func (aml *AdaptiveMLEngine) calculateTrend(recentPerformance []float64) string {
	if len(recentPerformance) < 10 {
		return "stable"
	}

	// Calcular tendencia de últimas 10 vs primeras 10
	recent10 := recentPerformance[len(recentPerformance)-10:]
	first10 := recentPerformance[:10]

	recentAvg := 0.0
	firstAvg := 0.0

	for _, val := range recent10 {
		recentAvg += val
	}
	recentAvg /= 10.0

	for _, val := range first10 {
		firstAvg += val
	}
	firstAvg /= 10.0

	diff := recentAvg - firstAvg
	if diff > 0.1 {
		return "improving"
	} else if diff < -0.1 {
		return "declining"
	}

	return "stable"
}

// adaptStrategyParameters adapta parámetros de estrategia basado en performance
func (aml *AdaptiveMLEngine) adaptStrategyParameters(strategy *Strategy, perf *StrategyPerformance) {
	if perf.TrendDirection == "declining" && perf.SuccessRate < 0.3 {
		// Estrategia declining - reducir confianza y ajustar parámetros
		strategy.Confidence *= 0.9

		// Ajustar parámetros específicos según tipo
		switch strategy.Type {
		case "gap_analysis":
			if minGap, exists := strategy.Parameters["min_gap"]; exists {
				strategy.Parameters["min_gap"] = minGap * 1.1 // Ser más restrictivo
			}
		case "frequency_analysis":
			if threshold, exists := strategy.Parameters["hot_threshold"]; exists {
				strategy.Parameters["hot_threshold"] = threshold * 1.1
			}
		}
	} else if perf.TrendDirection == "improving" && perf.SuccessRate > 0.6 {
		// Estrategia improving - aumentar confianza
		strategy.Confidence = math.Min(strategy.Confidence*1.05, 1.0)

		// Hacer parámetros más agresivos
		switch strategy.Type {
		case "gap_analysis":
			if minGap, exists := strategy.Parameters["min_gap"]; exists {
				strategy.Parameters["min_gap"] = math.Max(minGap*0.95, 5.0)
			}
		case "frequency_analysis":
			if threshold, exists := strategy.Parameters["hot_threshold"]; exists {
				strategy.Parameters["hot_threshold"] = math.Max(threshold*0.95, 0.02)
			}
		}
	}

	log.Printf("📈 Estrategia %s adaptada: confidence=%.3f, trend=%s, success_rate=%.3f",
		strategy.ID, strategy.Confidence, perf.TrendDirection, perf.SuccessRate)
}

// continuousAdaptation proceso continuo de adaptación
func (aml *AdaptiveMLEngine) continuousAdaptation() {
	ticker := time.NewTicker(aml.adaptationPeriod)
	defer ticker.Stop()

	for range ticker.C {
		aml.performAdaptation()
	}
}

// performAdaptation realiza adaptación periódica
func (aml *AdaptiveMLEngine) performAdaptation() {
	log.Println("🔄 Realizando adaptación de estrategias ML...")

	aml.mutex.Lock()
	defer aml.mutex.Unlock()

	// Analizar performance de todas las estrategias
	for strategyID, strategy := range aml.Strategies {
		if perf, exists := aml.PerformanceTrack[strategyID]; exists {
			// Si una estrategia está muy mal, crear variación
			if perf.SuccessRate < 0.2 && perf.TotalUses > 50 {
				aml.createStrategyVariation(strategy)
			}

			// Si una estrategia está muy bien, crear variaciones similares
			if perf.SuccessRate > 0.7 && perf.TotalUses > 30 {
				aml.createSuccessfulVariation(strategy)
			}
		}
	}

	// Eliminar estrategias muy malas
	aml.prunePoorStrategies()

	// Guardar cambios
	aml.saveStrategiesToRedis()
	aml.savePerformanceToRedis()

	log.Printf("✅ Adaptación completada. Total estrategias: %d", len(aml.Strategies))
}

// createStrategyVariation crea variación de estrategia fallida
func (aml *AdaptiveMLEngine) createStrategyVariation(originalStrategy *Strategy) {
	newStrategy := &Strategy{
		ID:   fmt.Sprintf("%s_v%d", originalStrategy.ID, time.Now().Unix()%1000),
		Name: fmt.Sprintf("%s Variation", originalStrategy.Name),
		Type: originalStrategy.Type,
		Parameters: make(map[string]float64),
		Conditions: make([]StrategyCondition, len(originalStrategy.Conditions)),
		Actions: make([]StrategyAction, len(originalStrategy.Actions)),
		Confidence: originalStrategy.Confidence * 0.7, // Empezar con menos confianza
		Created: time.Now(),
		LastUpdated: time.Now(),
		SuccessRate: 0.0,
		TotalPredictions: 0,
	}

	// Copiar y mutar parámetros
	for key, value := range originalStrategy.Parameters {
		// Mutación aleatoria ±20%
		mutation := 1.0 + (0.4*aml.randomFloat() - 0.2)
		newStrategy.Parameters[key] = value * mutation
	}

	// Copiar condiciones con mutación
	copy(newStrategy.Conditions, originalStrategy.Conditions)
	for i := range newStrategy.Conditions {
		// Mutar valores de condiciones
		mutation := 1.0 + (0.3*aml.randomFloat() - 0.15)
		newStrategy.Conditions[i].Value *= mutation
	}

	// Copiar acciones
	copy(newStrategy.Actions, originalStrategy.Actions)

	// Agregar nueva estrategia
	aml.Strategies[newStrategy.ID] = newStrategy
	aml.PerformanceTrack[newStrategy.ID] = &StrategyPerformance{
		StrategyID:        newStrategy.ID,
		TotalUses:         0,
		SuccessfulHits:    0,
		SuccessRate:       0.0,
		AverageConfidence: newStrategy.Confidence,
		LastUsed:          time.Now(),
		RecentPerformance: []float64{},
		TrendDirection:    "stable",
	}

	log.Printf("🧬 Creada variación de estrategia: %s", newStrategy.ID)
}

// createSuccessfulVariation crea variación de estrategia exitosa
func (aml *AdaptiveMLEngine) createSuccessfulVariation(originalStrategy *Strategy) {
	newStrategy := &Strategy{
		ID:   fmt.Sprintf("%s_success_v%d", originalStrategy.ID, time.Now().Unix()%1000),
		Name: fmt.Sprintf("%s Success Variant", originalStrategy.Name),
		Type: originalStrategy.Type,
		Parameters: make(map[string]float64),
		Conditions: make([]StrategyCondition, len(originalStrategy.Conditions)),
		Actions: make([]StrategyAction, len(originalStrategy.Actions)),
		Confidence: math.Min(originalStrategy.Confidence*1.1, 1.0), // Más confianza
		Created: time.Now(),
		LastUpdated: time.Now(),
		SuccessRate: 0.0,
		TotalPredictions: 0,
	}

	// Copiar parámetros con pequeñas mejoras
	for key, value := range originalStrategy.Parameters {
		// Pequeña mutación ±10% para refinar
		mutation := 1.0 + (0.2*aml.randomFloat() - 0.1)
		newStrategy.Parameters[key] = value * mutation
	}

	// Copiar condiciones con refinamiento
	copy(newStrategy.Conditions, originalStrategy.Conditions)
	for i := range newStrategy.Conditions {
		// Pequeña mutación para refinar
		mutation := 1.0 + (0.15*aml.randomFloat() - 0.075)
		newStrategy.Conditions[i].Value *= mutation
	}

	copy(newStrategy.Actions, originalStrategy.Actions)

	aml.Strategies[newStrategy.ID] = newStrategy
	aml.PerformanceTrack[newStrategy.ID] = &StrategyPerformance{
		StrategyID:        newStrategy.ID,
		TotalUses:         0,
		SuccessfulHits:    0,
		SuccessRate:       0.0,
		AverageConfidence: newStrategy.Confidence,
		LastUsed:          time.Now(),
		RecentPerformance: []float64{},
		TrendDirection:    "stable",
	}

	log.Printf("⭐ Creada variación exitosa de estrategia: %s", newStrategy.ID)
}

// prunePoorStrategies elimina estrategias con mal rendimiento
func (aml *AdaptiveMLEngine) prunePoorStrategies() {
	toDelete := []string{}

	for strategyID, perf := range aml.PerformanceTrack {
		// Eliminar estrategias muy malas con suficientes datos
		if perf.SuccessRate < 0.15 && perf.TotalUses > 100 {
			toDelete = append(toDelete, strategyID)
		}

		// Eliminar estrategias no usadas en mucho tiempo
		if time.Since(perf.LastUsed) > time.Hour*24 && perf.TotalUses > 0 {
			toDelete = append(toDelete, strategyID)
		}
	}

	// Mantener al menos 3 estrategias
	if len(aml.Strategies)-len(toDelete) < 3 {
		toDelete = toDelete[:len(aml.Strategies)-3]
	}

	for _, strategyID := range toDelete {
		delete(aml.Strategies, strategyID)
		delete(aml.PerformanceTrack, strategyID)
		log.Printf("🗑️ Eliminada estrategia pobre: %s", strategyID)
	}
}

// randomFloat genera float aleatorio entre 0 y 1
func (aml *AdaptiveMLEngine) randomFloat() float64 {
	return float64(time.Now().UnixNano()%1000) / 1000.0
}

// saveStrategiesToRedis guarda estrategias en Redis
func (aml *AdaptiveMLEngine) saveStrategiesToRedis() {
	ctx := context.Background()

	for strategyID, strategy := range aml.Strategies {
		strategyJSON, err := json.Marshal(strategy)
		if err == nil {
			aml.RedisClient.Set(ctx, fmt.Sprintf("ml:strategies:%s", strategyID), strategyJSON, time.Hour*24)
		}
	}
}

// savePerformanceToRedis guarda métricas de performance en Redis
func (aml *AdaptiveMLEngine) savePerformanceToRedis() {
	ctx := context.Background()

	for strategyID, perf := range aml.PerformanceTrack {
		perfJSON, err := json.Marshal(perf)
		if err == nil {
			aml.RedisClient.Set(ctx, fmt.Sprintf("ml:performance:%s", strategyID), perfJSON, time.Hour*24)
		}
	}
}

// loadStrategiesFromRedis carga estrategias desde Redis
func (aml *AdaptiveMLEngine) loadStrategiesFromRedis() {
	ctx := context.Background()

	keys, err := aml.RedisClient.Keys(ctx, "ml:strategies:*").Result()
	if err != nil {
		return
	}

	for _, key := range keys {
		strategyJSON, err := aml.RedisClient.Get(ctx, key).Result()
		if err == nil {
			var strategy Strategy
			if json.Unmarshal([]byte(strategyJSON), &strategy) == nil {
				aml.Strategies[strategy.ID] = &strategy
			}
		}
	}

	// Cargar performance
	perfKeys, err := aml.RedisClient.Keys(ctx, "ml:performance:*").Result()
	if err != nil {
		return
	}

	for _, key := range perfKeys {
		perfJSON, err := aml.RedisClient.Get(ctx, key).Result()
		if err == nil {
			var perf StrategyPerformance
			if json.Unmarshal([]byte(perfJSON), &perf) == nil {
				aml.PerformanceTrack[perf.StrategyID] = &perf
			}
		}
	}

	log.Printf("📚 Cargadas %d estrategias y %d métricas de performance desde Redis",
		len(aml.Strategies), len(aml.PerformanceTrack))
}

// GetStrategyPerformanceReport genera reporte de performance
func (aml *AdaptiveMLEngine) GetStrategyPerformanceReport() map[string]interface{} {
	aml.mutex.RLock()
	defer aml.mutex.RUnlock()

	report := map[string]interface{}{
		"total_strategies": len(aml.Strategies),
		"strategies": make([]map[string]interface{}, 0),
		"summary": map[string]interface{}{
			"best_strategy": "",
			"worst_strategy": "",
			"average_success_rate": 0.0,
			"total_predictions": 0,
		},
		"timestamp": time.Now().Format(time.RFC3339),
	}

	bestRate := 0.0
	worstRate := 1.0
	totalSuccessRate := 0.0
	totalPredictions := 0
	bestStrategy := ""
	worstStrategy := ""

	strategies := make([]map[string]interface{}, 0, len(aml.Strategies))

	for strategyID, strategy := range aml.Strategies {
		if perf, exists := aml.PerformanceTrack[strategyID]; exists {
			strategyInfo := map[string]interface{}{
				"id": strategyID,
				"name": strategy.Name,
				"type": strategy.Type,
				"confidence": strategy.Confidence,
				"success_rate": perf.SuccessRate,
				"total_uses": perf.TotalUses,
				"trend": perf.TrendDirection,
				"last_used": perf.LastUsed.Format(time.RFC3339),
			}

			strategies = append(strategies, strategyInfo)

			// Actualizar summary
			if perf.SuccessRate > bestRate && perf.TotalUses > 10 {
				bestRate = perf.SuccessRate
				bestStrategy = strategyID
			}

			if perf.SuccessRate < worstRate && perf.TotalUses > 10 {
				worstRate = perf.SuccessRate
				worstStrategy = strategyID
			}

			totalSuccessRate += perf.SuccessRate
			totalPredictions += perf.TotalUses
		}
	}

	// Ordenar por success rate
	sort.Slice(strategies, func(i, j int) bool {
		stratI := strategies[i]
		stratJ := strategies[j]
		rateI, okI := stratI["success_rate"].(float64)
		rateJ, okJ := stratJ["success_rate"].(float64)
		if !okI || !okJ {
			return false
		}
		return rateI > rateJ
	})

	report["strategies"] = strategies
	summary := report["summary"].(map[string]interface{})
	summary["best_strategy"] = bestStrategy
	summary["worst_strategy"] = worstStrategy
	if len(aml.Strategies) > 0 {
		summary["average_success_rate"] = totalSuccessRate / float64(len(aml.Strategies))
	}
	summary["total_predictions"] = totalPredictions

	return report
}