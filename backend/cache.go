package main

import (
	"crypto/sha256"
	"encoding/hex"
	"sync"
	"time"
)

// CacheItem representa un elemento en el cache
type CacheItem struct {
	Value      interface{}
	Expiration time.Time
}

// IsExpired verifica si el item ha expirado
func (item *CacheItem) IsExpired() bool {
	return time.Now().After(item.Expiration)
}

// FastCache implementa un cache ultrarrápido en memoria con concurrencia
type FastCache struct {
	items map[string]*CacheItem
	mutex sync.RWMutex
	ttl   time.Duration
}

// NewFastCache crea un nuevo cache rápido
func NewFastCache(ttl time.Duration) *FastCache {
	return &FastCache{
		items: make(map[string]*CacheItem),
		ttl:   ttl,
	}
}

// Set almacena un valor en el cache
func (c *FastCache) Set(key string, value interface{}) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.items[key] = &CacheItem{
		Value:      value,
		Expiration: time.Now().Add(c.ttl),
	}
}

// Get obtiene un valor del cache
func (c *FastCache) Get(key string) (interface{}, bool) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	item, exists := c.items[key]
	if !exists {
		return nil, false
	}

	if item.IsExpired() {
		// Eliminar item expirado (será limpiado en la próxima limpieza)
		return nil, false
	}

	return item.Value, true
}

// Delete elimina un valor del cache
func (c *FastCache) Delete(key string) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	delete(c.items, key)
}

// Cleanup elimina items expirados del cache
func (c *FastCache) Cleanup() {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	now := time.Now()
	expiredKeys := make([]string, 0)

	for key, item := range c.items {
		if now.After(item.Expiration) {
			expiredKeys = append(expiredKeys, key)
		}
	}

	for _, key := range expiredKeys {
		delete(c.items, key)
	}

	if len(expiredKeys) > 0 {
		// log.Printf("🧹 Cache cleanup: eliminados %d items expirados", len(expiredKeys))
	}
}

// Size retorna el número de items en el cache
func (c *FastCache) Size() int {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	return len(c.items)
}

// Clear limpia todo el cache
func (c *FastCache) Clear() {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	c.items = make(map[string]*CacheItem)
}

// GenerateKey genera una clave única basada en múltiples parámetros
func GenerateKey(params ...interface{}) string {
	h := sha256.New()
	for _, param := range params {
		h.Write([]byte(InterfaceToString(param)))
	}
	return hex.EncodeToString(h.Sum(nil))[:16] // Solo primeros 16 chars para rapidez
}

// InterfaceToString convierte interface{} a string de manera segura
func InterfaceToString(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	case int:
		return string(rune(val))
	case []int:
		result := ""
		for _, i := range val {
			result += string(rune(i))
		}
		return result
	default:
		return ""
	}
}

// PredictionCache especializa el cache para predicciones
type PredictionCache struct {
	*FastCache
}

// NewPredictionCache crea un cache especializado para predicciones
func NewPredictionCache() *PredictionCache {
	return &PredictionCache{
		FastCache: NewFastCache(time.Minute * 2), // TTL corto para predicciones
	}
}

// SetPrediction guarda una predicción en cache
func (pc *PredictionCache) SetPrediction(history []int, predictionType string, result *PredictionResult) {
	key := GenerateKey("prediction", history, predictionType)
	pc.Set(key, result)
}

// GetPrediction obtiene una predicción del cache
func (pc *PredictionCache) GetPrediction(history []int, predictionType string) (*PredictionResult, bool) {
	key := GenerateKey("prediction", history, predictionType)
	if value, exists := pc.Get(key); exists {
		if result, ok := value.(*PredictionResult); ok {
			return result, true
		}
	}
	return nil, false
}

// FeatureCache especializa el cache para features
type FeatureCache struct {
	*FastCache
}

// NewFeatureCache crea un cache especializado para features
func NewFeatureCache() *FeatureCache {
	return &FeatureCache{
		FastCache: NewFastCache(time.Minute * 5), // TTL más largo para features
	}
}

// SetFeatures guarda features en cache
func (fc *FeatureCache) SetFeatures(history []int, features map[string]interface{}) {
	key := GenerateKey("features", history)
	fc.Set(key, features)
}

// GetFeatures obtiene features del cache
func (fc *FeatureCache) GetFeatures(history []int) (map[string]interface{}, bool) {
	key := GenerateKey("features", history)
	if value, exists := fc.Get(key); exists {
		if features, ok := value.(map[string]interface{}); ok {
			return features, true
		}
	}
	return nil, false
}