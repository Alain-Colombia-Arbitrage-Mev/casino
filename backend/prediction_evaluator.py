import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

class PredictionEvaluator:
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client
        self.evaluation_history = defaultdict(list)
        self.group_statistics = {
            'individual': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0},
            'grupo_5': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0},
            'grupo_10': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0},
            'grupo_12': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0},
            'grupo_15': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0},
            'grupo_20': {'aciertos': 0, 'total': 0, 'porcentaje': 0.0}
        }
        
    def evaluate_prediction(self, prediction_data, actual_number):
        """
        Evalúa una predicción contra el número real que salió
        
        Args:
            prediction_data: Diccionario con las predicciones (individual, grupos, etc.)
            actual_number: El número que realmente salió
            
        Returns:
            Diccionario con los resultados de la evaluación
        """
        evaluation_result = {
            'timestamp': datetime.now().isoformat(),
            'actual_number': actual_number,
            'prediction_data': prediction_data,
            'results': {},
            'summary': {}
        }
        
        # Evaluar predicción individual
        individual_pred = prediction_data.get('individual', None)
        if individual_pred is not None:
            individual_hit = (individual_pred == actual_number)
            evaluation_result['results']['individual'] = {
                'predicted': individual_pred,
                'hit': individual_hit,
                'type': 'individual'
            }
            self._update_group_stats('individual', individual_hit)
        
        # Evaluar grupos de predicción
        groups_to_evaluate = ['grupo_5', 'grupo_10', 'grupo_12', 'grupo_15', 'grupo_20']
        
        for group_name in groups_to_evaluate:
            group_pred = prediction_data.get(group_name, [])
            if isinstance(group_pred, list) and len(group_pred) > 0:
                group_hit = actual_number in group_pred
                evaluation_result['results'][group_name] = {
                    'predicted_numbers': group_pred,
                    'hit': group_hit,
                    'type': 'group',
                    'group_size': len(group_pred)
                }
                self._update_group_stats(group_name, group_hit)
        
        # Evaluar predicciones ML específicas
        ml_predictions = prediction_data.get('ml_predictions', {})
        if ml_predictions:
            for model_name, model_pred in ml_predictions.items():
                if isinstance(model_pred, int):
                    ml_hit = (model_pred == actual_number)
                    evaluation_result['results'][f'ml_{model_name}'] = {
                        'predicted': model_pred,
                        'hit': ml_hit,
                        'type': 'ml_model'
                    }
        
        # Evaluar estrategias
        strategy_predictions = prediction_data.get('strategy_predictions', {})
        if strategy_predictions:
            for strategy_name, strategy_numbers in strategy_predictions.items():
                if isinstance(strategy_numbers, list) and len(strategy_numbers) > 0:
                    strategy_hit = actual_number in strategy_numbers
                    evaluation_result['results'][f'strategy_{strategy_name}'] = {
                        'predicted_numbers': strategy_numbers,
                        'hit': strategy_hit,
                        'type': 'strategy'
                    }
        
        # Evaluar sectores
        sector_predictions = prediction_data.get('sector_predictions', {})
        if sector_predictions:
            for sector_name, sector_numbers in sector_predictions.items():
                if isinstance(sector_numbers, list) and len(sector_numbers) > 0:
                    sector_hit = actual_number in sector_numbers
                    evaluation_result['results'][f'sector_{sector_name}'] = {
                        'predicted_numbers': sector_numbers,
                        'hit': sector_hit,
                        'type': 'sector'
                    }
        
        # Generar resumen
        evaluation_result['summary'] = self._generate_evaluation_summary(evaluation_result['results'])
        
        # Guardar evaluación en historial
        self.evaluation_history[datetime.now().date()].append(evaluation_result)
        
        # Guardar en base de datos si está disponible
        if self.supabase_client:
            self._save_evaluation_to_db(evaluation_result)
        
        return evaluation_result
    
    def _update_group_stats(self, group_name, hit):
        """Actualiza las estadísticas de aciertos por grupo"""
        if group_name in self.group_statistics:
            self.group_statistics[group_name]['total'] += 1
            if hit:
                self.group_statistics[group_name]['aciertos'] += 1
            
            # Recalcular porcentaje
            total = self.group_statistics[group_name]['total']
            aciertos = self.group_statistics[group_name]['aciertos']
            self.group_statistics[group_name]['porcentaje'] = (aciertos / total * 100) if total > 0 else 0.0
    
    def _generate_evaluation_summary(self, results):
        """Genera un resumen de la evaluación"""
        summary = {
            'total_predictions': len(results),
            'hits': 0,
            'misses': 0,
            'hit_rate': 0.0,
            'best_performers': [],
            'group_performance': {},
            'ml_performance': {},
            'strategy_performance': {},
            'sector_performance': {}
        }
        
        # Contar aciertos y fallos
        for pred_name, pred_result in results.items():
            if pred_result['hit']:
                summary['hits'] += 1
            else:
                summary['misses'] += 1
        
        # Calcular tasa de aciertos general
        if summary['total_predictions'] > 0:
            summary['hit_rate'] = (summary['hits'] / summary['total_predictions']) * 100
        
        # Agrupar rendimiento por tipo
        for pred_name, pred_result in results.items():
            pred_type = pred_result['type']
            
            if pred_type == 'group':
                summary['group_performance'][pred_name] = pred_result['hit']
            elif pred_type == 'ml_model':
                summary['ml_performance'][pred_name] = pred_result['hit']
            elif pred_type == 'strategy':
                summary['strategy_performance'][pred_name] = pred_result['hit']
            elif pred_type == 'sector':
                summary['sector_performance'][pred_name] = pred_result['hit']
        
        # Identificar mejores predictores
        summary['best_performers'] = [
            name for name, result in results.items() if result['hit']
        ]
        
        return summary
    
    def get_group_statistics(self):
        """Retorna las estadísticas actuales por grupo"""
        return self.group_statistics.copy()
    
    def get_recent_performance(self, days=7):
        """Obtiene el rendimiento de los últimos N días"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_evaluations = []
        
        for date, evaluations in self.evaluation_history.items():
            if date >= cutoff_date:
                recent_evaluations.extend(evaluations)
        
        return self._analyze_performance(recent_evaluations)
    
    def _analyze_performance(self, evaluations):
        """Analiza el rendimiento de una lista de evaluaciones"""
        if not evaluations:
            return {'error': 'No hay evaluaciones para analizar'}
        
        analysis = {
            'total_evaluations': len(evaluations),
            'group_analysis': defaultdict(lambda: {'hits': 0, 'total': 0, 'rate': 0.0}),
            'ml_analysis': defaultdict(lambda: {'hits': 0, 'total': 0, 'rate': 0.0}),
            'strategy_analysis': defaultdict(lambda: {'hits': 0, 'total': 0, 'rate': 0.0}),
            'sector_analysis': defaultdict(lambda: {'hits': 0, 'total': 0, 'rate': 0.0}),
            'best_groups': [],
            'worst_groups': [],
            'recommendations': []
        }
        
        # Analizar cada evaluación
        for evaluation in evaluations:
            for pred_name, pred_result in evaluation['results'].items():
                pred_type = pred_result['type']
                hit = pred_result['hit']
                
                if pred_type == 'group':
                    analysis['group_analysis'][pred_name]['total'] += 1
                    if hit:
                        analysis['group_analysis'][pred_name]['hits'] += 1
                elif pred_type == 'ml_model':
                    analysis['ml_analysis'][pred_name]['total'] += 1
                    if hit:
                        analysis['ml_analysis'][pred_name]['hits'] += 1
                elif pred_type == 'strategy':
                    analysis['strategy_analysis'][pred_name]['total'] += 1
                    if hit:
                        analysis['strategy_analysis'][pred_name]['hits'] += 1
                elif pred_type == 'sector':
                    analysis['sector_analysis'][pred_name]['total'] += 1
                    if hit:
                        analysis['sector_analysis'][pred_name]['hits'] += 1
        
        # Calcular tasas de acierto
        for category in ['group_analysis', 'ml_analysis', 'strategy_analysis', 'sector_analysis']:
            for name, stats in analysis[category].items():
                if stats['total'] > 0:
                    stats['rate'] = (stats['hits'] / stats['total']) * 100
        
        # Identificar mejores y peores grupos
        group_rates = [(name, stats['rate']) for name, stats in analysis['group_analysis'].items()]
        group_rates.sort(key=lambda x: x[1], reverse=True)
        
        analysis['best_groups'] = group_rates[:3]
        analysis['worst_groups'] = group_rates[-3:]
        
        # Generar recomendaciones
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis):
        """Genera recomendaciones basadas en el análisis de rendimiento"""
        recommendations = []
        
        # Recomendaciones basadas en grupos
        if analysis['group_analysis']:
            best_group = max(analysis['group_analysis'].items(), key=lambda x: x[1]['rate'])
            if best_group[1]['rate'] > 30:  # Si tiene más de 30% de aciertos
                recommendations.append({
                    'tipo': 'grupo_recomendado',
                    'mensaje': f'El {best_group[0]} tiene la mejor tasa de aciertos ({best_group[1]["rate"]:.1f}%)',
                    'accion': f'Considere apostar principalmente al {best_group[0]}'
                })
        
        # Recomendaciones basadas en ML
        if analysis['ml_analysis']:
            best_ml = max(analysis['ml_analysis'].items(), key=lambda x: x[1]['rate'])
            if best_ml[1]['rate'] > 15:  # Si tiene más de 15% de aciertos para predicción individual
                recommendations.append({
                    'tipo': 'modelo_ml_recomendado',
                    'mensaje': f'El modelo {best_ml[0]} es el más preciso ({best_ml[1]["rate"]:.1f}%)',
                    'accion': f'Priorice las predicciones del modelo {best_ml[0]}'
                })
        
        # Recomendaciones basadas en estrategias
        if analysis['strategy_analysis']:
            active_strategies = [name for name, stats in analysis['strategy_analysis'].items() if stats['rate'] > 25]
            if active_strategies:
                recommendations.append({
                    'tipo': 'estrategias_activas',
                    'mensaje': f'Las estrategias {", ".join(active_strategies)} están funcionando bien',
                    'accion': 'Mantenga el seguimiento de estas estrategias'
                })
        
        return recommendations
    
    def _save_evaluation_to_db(self, evaluation_result):
        """Guarda la evaluación en la base de datos"""
        if not self.supabase_client:
            return False
        
        try:
            # Preparar datos para guardar
            db_data = {
                'timestamp': evaluation_result['timestamp'],
                'actual_number': evaluation_result['actual_number'],
                'prediction_data': json.dumps(evaluation_result['prediction_data']),
                'results': json.dumps(evaluation_result['results']),
                'summary': json.dumps(evaluation_result['summary']),
                'created_at': datetime.now().isoformat()
            }
            
            # Insertar en tabla de evaluaciones
            response = self.supabase_client.table('prediction_evaluations').insert(db_data).execute()
            
            if response.data:
                print(f"✅ Evaluación guardada en DB con ID: {response.data[0].get('id', 'N/A')}")
                return True
            else:
                print("⚠️ No se recibió confirmación al guardar evaluación")
                return False
                
        except Exception as e:
            print(f"❌ Error al guardar evaluación en DB: {e}")
            return False
    
    def load_statistics_from_db(self, days=30):
        """Carga estadísticas desde la base de datos"""
        if not self.supabase_client:
            return False
        
        try:
            # Obtener evaluaciones de los últimos N días
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.supabase_client.table('prediction_evaluations')\
                .select('*')\
                .gte('created_at', cutoff_date)\
                .order('created_at', desc=False)\
                .execute()
            
            if response.data:
                # Procesar evaluaciones cargadas
                for row in response.data:
                    try:
                        results = json.loads(row['results'])
                        
                        # Actualizar estadísticas de grupos
                        for pred_name, pred_result in results.items():
                            if pred_result['type'] == 'group' and pred_name in self.group_statistics:
                                self._update_group_stats(pred_name, pred_result['hit'])
                                
                    except json.JSONDecodeError as e:
                        print(f"Error al parsear resultados de evaluación: {e}")
                        continue
                
                print(f"✅ Cargadas {len(response.data)} evaluaciones desde la DB")
                return True
            else:
                print("No se encontraron evaluaciones en la DB")
                return False
                
        except Exception as e:
            print(f"❌ Error al cargar estadísticas desde DB: {e}")
            return False
    
    def reset_statistics(self):
        """Reinicia todas las estadísticas"""
        for group_name in self.group_statistics:
            self.group_statistics[group_name] = {'aciertos': 0, 'total': 0, 'porcentaje': 0.0}
        
        self.evaluation_history.clear()
        print("📊 Estadísticas reiniciadas")

    def export_statistics(self):
        """Exporta las estadísticas actuales"""
        return {
            'group_statistics': self.group_statistics,
            'evaluation_count': sum(len(evals) for evals in self.evaluation_history.values()),
            'last_updated': datetime.now().isoformat()
        } 