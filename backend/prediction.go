package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"
)

// PredictionResult estructura del resultado de predicción
type PredictionResult struct {
	PredictionID     string                 `json:"prediction_id"`
	Timestamp        string                 `json:"timestamp"`
	LastNumber       int                    `json:"last_number"`
	PredictedNumbers []int                  `json:"predicted_numbers"`
	PredictionGroups map[string][]int       `json:"prediction_groups"`
	PredictionType   string                 `json:"prediction_type"`
	Confidence       float64                `json:"confidence"`
	Reasoning        string                 `json:"reasoning"`
	ModelUsed        string                 `json:"model_used"`
	Probabilities    map[int]float64        `json:"probabilities"`
}

// RoulettePredictor estructura principal del predictor
type RoulettePredictor struct {
	PredictionCache *PredictionCache
	FeatureCache    *FeatureCache
	ModelCache      *FastCache
}

// NewRoulettePredictor crea un nuevo predictor
func NewRoulettePredictor() *RoulettePredictor {
	return &RoulettePredictor{
		PredictionCache: NewPredictionCache(),
		FeatureCache:    NewFeatureCache(),
		ModelCache:      NewFastCache(time.Hour), // Modelos se cachean por 1 hora
	}
}

// PredictEnsemble hace predicción usando ensemble ultrarrápido
func (rp *RoulettePredictor) PredictEnsemble(history []int, predictionType string) (*PredictionResult, error) {
	if len(history) < 5 {
		return rp.createBasicFallback(predictionType), nil
	}

	// 1. Verificar cache primero (súper rápido - <1ms)
	if cached, exists := rp.PredictionCache.GetPrediction(history[:10], predictionType); exists {
		return cached, nil
	}

	// 2. Extraer features (optimizado con cache)
	features := rp.extractFeatures(history)

	// 3. Hacer predicción usando múltiples modelos en paralelo
	result := rp.ensemblePredict(history, features, predictionType)

	// 4. Guardar en cache para próximas consultas
	rp.PredictionCache.SetPrediction(history[:10], predictionType, result)

	return result, nil
}

// extractFeatures extrae características del historial (optimizado)
func (rp *RoulettePredictor) extractFeatures(history []int) map[string]interface{} {
	// Verificar cache de features primero
	cacheLen := min(len(history), 20)
	if cached, exists := rp.FeatureCache.GetFeatures(history[:cacheLen]); exists {
		return cached
	}

	features := make(map[string]interface{})

	// Features básicas optimizadas
	features["last_number"] = history[0]
	features["sequence_length"] = len(history)

	// Análisis de frecuencias rápido
	freq := make(map[int]int)
	for _, num := range history[:min(len(history), 30)] { // Solo últimos 30
		freq[num]++
	}

	// Features estadísticas
	features["most_frequent"] = getMostFrequent(freq)
	features["unique_count"] = len(freq)

	// Patrones rápidos
	patternLen := min(len(history), 20)
	features["red_count"] = countRedNumbers(history[:patternLen])
	features["black_count"] = countBlackNumbers(history[:patternLen])
	features["even_count"] = countEvenNumbers(history[:patternLen])
	features["odd_count"] = countOddNumbers(history[:patternLen])

	// Tendencias recientes (últimos 10)
	recent := history[:min(len(history), 10)]
	features["recent_avg"] = average(recent)
	features["recent_variance"] = variance(recent)

	// Gaps (optimizado)
	gapLen := min(len(history), 25)
	features["gaps"] = calculateGaps(history[:gapLen])

	// Features temporales
	now := time.Now()
	features["hour"] = now.Hour()
	features["minute"] = now.Minute()

	// Guardar en cache
	rp.FeatureCache.SetFeatures(history[:cacheLen], features)

	return features
}

// ensemblePredict realiza predicción usando ensemble de modelos
func (rp *RoulettePredictor) ensemblePredict(history []int, features map[string]interface{}, predictionType string) *PredictionResult {
	// Modelos rápidos en paralelo
	resultsChan := make(chan modelResult, 4)

	// Ejecutar modelos en paralelo
	go func() { resultsChan <- rp.frequencyModel(history) }()
	go func() { resultsChan <- rp.patternModel(history) }()
	go func() { resultsChan <- rp.trendModel(history) }()
	go func() { resultsChan <- rp.statisticalModel(history) }()

	// Recolectar resultados
	results := make([]modelResult, 0, 4)
	for i := 0; i < 4; i++ {
		results = append(results, <-resultsChan)
	}

	// Combinar predicciones
	finalPrediction := rp.combineResults(results, history, predictionType)

	return finalPrediction
}

// modelResult estructura para resultados de modelos individuales
type modelResult struct {
	Numbers     []int
	Confidence  float64
	ModelName   string
	Probabilities map[int]float64
}

// frequencyModel modelo basado en frecuencias
func (rp *RoulettePredictor) frequencyModel(history []int) modelResult {
	freq := make(map[int]int)
	for _, num := range history[:min(len(history), 50)] {
		freq[num]++
	}

	// Ordenar por frecuencia
	type pair struct {
		num   int
		count int
	}

	pairs := make([]pair, 0, len(freq))
	for num, count := range freq {
		pairs = append(pairs, pair{num, count})
	}

	sort.Slice(pairs, func(i, j int) bool {
		return pairs[i].count > pairs[j].count
	})

	// Top 6
	numbers := make([]int, 0, 6)
	probs := make(map[int]float64)
	total := float64(len(history))

	for i := 0; i < min(len(pairs), 6); i++ {
		numbers = append(numbers, pairs[i].num)
		probs[pairs[i].num] = float64(pairs[i].count) / total
	}

	return modelResult{
		Numbers:       numbers,
		Confidence:    0.7,
		ModelName:     "frequency",
		Probabilities: probs,
	}
}

// patternModel modelo basado en patrones
func (rp *RoulettePredictor) patternModel(history []int) modelResult {
	if len(history) < 10 {
		return rp.randomModel()
	}

	// Buscar patrones en secuencias de 3
	patterns := make(map[string][]int)
	for i := 0; i < len(history)-3; i++ {
		pattern := fmt.Sprintf("%d-%d-%d", history[i], history[i+1], history[i+2])
		if i+3 < len(history) {
			patterns[pattern] = append(patterns[pattern], history[i+3])
		}
	}

	// Encontrar el patrón más reciente
	lastPattern := fmt.Sprintf("%d-%d-%d", history[0], history[1], history[2])

	var numbers []int
	if nextNums, exists := patterns[lastPattern]; exists && len(nextNums) > 0 {
		// Usar números que siguieron a este patrón
		freqMap := make(map[int]int)
		for _, num := range nextNums {
			freqMap[num]++
		}

		for num := range freqMap {
			numbers = append(numbers, num)
			if len(numbers) >= 6 {
				break
			}
		}
	}

	if len(numbers) == 0 {
		return rp.randomModel()
	}

	probs := make(map[int]float64)
	for _, num := range numbers {
		probs[num] = 0.6 / float64(len(numbers))
	}

	return modelResult{
		Numbers:       numbers,
		Confidence:    0.6,
		ModelName:     "pattern",
		Probabilities: probs,
	}
}

// trendModel modelo basado en tendencias
func (rp *RoulettePredictor) trendModel(history []int) modelResult {
	if len(history) < 15 {
		return rp.randomModel()
	}

	// Analizar tendencias en rangos
	recent := history[:10]
	avg := average(recent)

	// Predecir números cercanos al promedio
	numbers := make([]int, 0, 6)
	probs := make(map[int]float64)

	// Números alrededor del promedio
	center := int(avg)
	for offset := -2; offset <= 2; offset++ {
		num := center + offset
		if num >= 0 && num <= 36 {
			numbers = append(numbers, num)
			probs[num] = 0.5 / 6.0
		}
		if len(numbers) >= 6 {
			break
		}
	}

	// Agregar número más frecuente reciente si falta espacio
	if len(numbers) < 6 {
		freq := make(map[int]int)
		for _, num := range recent {
			freq[num]++
		}
		for num := range freq {
			if len(numbers) < 6 {
				exists := false
				for _, existing := range numbers {
					if existing == num {
						exists = true
						break
					}
				}
				if !exists {
					numbers = append(numbers, num)
					probs[num] = 0.4 / float64(len(numbers))
				}
			}
		}
	}

	return modelResult{
		Numbers:       numbers,
		Confidence:    0.5,
		ModelName:     "trend",
		Probabilities: probs,
	}
}

// statisticalModel modelo estadístico simple
func (rp *RoulettePredictor) statisticalModel(history []int) modelResult {
	// Distribución basada en gaps y probabilidades
	gaps := calculateGaps(history[:30])
	numbers := make([]int, 0, 6)
	probs := make(map[int]float64)

	// Números con gaps más grandes tienen más probabilidad
	type gapPair struct {
		num int
		gap int
	}

	gapList := make([]gapPair, 0)
	for num, gap := range gaps {
		gapList = append(gapList, gapPair{num, gap})
	}

	sort.Slice(gapList, func(i, j int) bool {
		return gapList[i].gap > gapList[j].gap
	})

	for i := 0; i < min(len(gapList), 6); i++ {
		numbers = append(numbers, gapList[i].num)
		probs[gapList[i].num] = 0.4 / 6.0
	}

	return modelResult{
		Numbers:       numbers,
		Confidence:    0.4,
		ModelName:     "statistical",
		Probabilities: probs,
	}
}

// randomModel modelo random de fallback
func (rp *RoulettePredictor) randomModel() modelResult {
	numbers := make([]int, 6)
	probs := make(map[int]float64)

	used := make(map[int]bool)
	for i := 0; i < 6; i++ {
		num := rand.Intn(37)
		for used[num] {
			num = rand.Intn(37)
		}
		numbers[i] = num
		used[num] = true
		probs[num] = 0.2 / 6.0
	}

	return modelResult{
		Numbers:       numbers,
		Confidence:    0.2,
		ModelName:     "random",
		Probabilities: probs,
	}
}

// combineResults combina resultados de múltiples modelos
func (rp *RoulettePredictor) combineResults(results []modelResult, history []int, predictionType string) *PredictionResult {
	// Combinar números con pesos por confianza
	numScores := make(map[int]float64)
	totalConfidence := 0.0

	for _, result := range results {
		for _, num := range result.Numbers {
			numScores[num] += result.Confidence
		}
		totalConfidence += result.Confidence
	}

	// Seleccionar top 6
	type scorePair struct {
		num   int
		score float64
	}

	scoreList := make([]scorePair, 0, len(numScores))
	for num, score := range numScores {
		scoreList = append(scoreList, scorePair{num, score})
	}

	sort.Slice(scoreList, func(i, j int) bool {
		return scoreList[i].score > scoreList[j].score
	})

	finalNumbers := make([]int, 0, 6)
	finalProbs := make(map[int]float64)

	for i := 0; i < min(len(scoreList), 6); i++ {
		finalNumbers = append(finalNumbers, scoreList[i].num)
		finalProbs[scoreList[i].num] = scoreList[i].score / totalConfidence
	}

	// Crear grupos
	groups := make(map[string][]int)
	groups["ensemble_top6"] = finalNumbers
	if len(finalNumbers) >= 4 {
		groups["ensemble_top4"] = finalNumbers[:4]
	}

	// Calcular confianza promedio
	avgConfidence := totalConfidence / float64(len(results))

	return &PredictionResult{
		PredictionID:     generatePredictionID("ensemble"),
		Timestamp:        time.Now().Format(time.RFC3339),
		LastNumber:       history[0],
		PredictedNumbers: finalNumbers,
		PredictionGroups: groups,
		PredictionType:   predictionType,
		Confidence:       avgConfidence,
		Reasoning:        fmt.Sprintf("Ensemble de %d modelos con confianza promedio %.2f", len(results), avgConfidence),
		ModelUsed:        "ensemble_go",
		Probabilities:    finalProbs,
	}
}

// createBasicFallback crea predicción básica de fallback
func (rp *RoulettePredictor) createBasicFallback(predictionType string) *PredictionResult {
	numbers := []int{7, 14, 21, 0, 35, 28}
	probs := make(map[int]float64)
	for _, num := range numbers {
		probs[num] = 1.0 / 37.0
	}

	groups := map[string][]int{
		"basic_fallback": numbers,
	}

	return &PredictionResult{
		PredictionID:     generatePredictionID("fallback"),
		Timestamp:        time.Now().Format(time.RFC3339),
		LastNumber:       0,
		PredictedNumbers: numbers,
		PredictionGroups: groups,
		PredictionType:   predictionType,
		Confidence:       0.1,
		Reasoning:        "Predicción básica de fallback",
		ModelUsed:        "basic_fallback_go",
		Probabilities:    probs,
	}
}

// Funciones auxiliares optimizadas
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func getMostFrequent(freq map[int]int) int {
	maxCount := 0
	mostFreq := 0
	for num, count := range freq {
		if count > maxCount {
			maxCount = count
			mostFreq = num
		}
	}
	return mostFreq
}

func countRedNumbers(history []int) int {
	redNumbers := map[int]bool{1: true, 3: true, 5: true, 7: true, 9: true, 12: true, 14: true, 16: true, 18: true, 19: true, 21: true, 23: true, 25: true, 27: true, 30: true, 32: true, 34: true, 36: true}
	count := 0
	for _, num := range history {
		if redNumbers[num] {
			count++
		}
	}
	return count
}

func countBlackNumbers(history []int) int {
	return len(history) - countRedNumbers(history) - countZeros(history)
}

func countZeros(history []int) int {
	count := 0
	for _, num := range history {
		if num == 0 {
			count++
		}
	}
	return count
}

func countEvenNumbers(history []int) int {
	count := 0
	for _, num := range history {
		if num != 0 && num%2 == 0 {
			count++
		}
	}
	return count
}

func countOddNumbers(history []int) int {
	count := 0
	for _, num := range history {
		if num%2 == 1 {
			count++
		}
	}
	return count
}

func average(nums []int) float64 {
	if len(nums) == 0 {
		return 0
	}
	sum := 0
	for _, num := range nums {
		sum += num
	}
	return float64(sum) / float64(len(nums))
}

func variance(nums []int) float64 {
	if len(nums) == 0 {
		return 0
	}
	avg := average(nums)
	sum := 0.0
	for _, num := range nums {
		diff := float64(num) - avg
		sum += diff * diff
	}
	return sum / float64(len(nums))
}

func calculateGaps(history []int) map[int]int {
	gaps := make(map[int]int)
	lastSeen := make(map[int]int)

	for i, num := range history {
		if lastPos, exists := lastSeen[num]; exists {
			gaps[num] = i - lastPos
		} else {
			gaps[num] = i + 1
		}
		lastSeen[num] = i
	}

	// Para números no vistos, asignar gap máximo
	for i := 0; i <= 36; i++ {
		if _, exists := gaps[i]; !exists {
			gaps[i] = len(history) + 1
		}
	}

	return gaps
}

func generatePredictionID(prefix string) string {
	timestamp := time.Now().Format("20060102_150405")
	random := rand.Intn(9999)
	return fmt.Sprintf("%s_%s_%04d", prefix, timestamp, random)
}