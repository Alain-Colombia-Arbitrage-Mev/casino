from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any, Optional
import re

# Import our new database manager
from database import db_manager

# Import existing ML components (we'll keep these)
from victory_trainer_fixed import VictoryTrainer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize ML components
victory_trainer = VictoryTrainer()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_roulette_number(number: int) -> bool:
    """Validate if number is valid for roulette (0-36)"""
    return isinstance(number, int) and 0 <= number <= 36

def parse_numbers_input(text: str) -> List[int]:
    """Parse text input to extract valid roulette numbers"""
    if not text or not text.strip():
        return []
    
    # Clean input
    cleaned = text.strip()
    
    # Handle single number
    if cleaned.isdigit():
        num = int(cleaned)
        return [num] if validate_roulette_number(num) else []
    
    # Handle multiple numbers (comma or space separated)
    # Replace multiple spaces with commas
    cleaned = re.sub(r'\s+', ',', cleaned)
    # Handle comma-space combinations
    cleaned = cleaned.replace(', ', ',')
    
    # Extract numbers
    numbers = []
    for part in cleaned.split(','):
        part = part.strip()
        if part.isdigit():
            num = int(part)
            if validate_roulette_number(num):
                numbers.append(num)
    
    return numbers

def check_consecutive_duplicates(number: int, recent_numbers: List[int]) -> Dict[str, Any]:
    """Check for consecutive duplicate numbers"""
    if not recent_numbers:
        return {'is_duplicate': False, 'message': ''}
    
    # Check immediate duplicate
    if recent_numbers[0] == number:
        return {
            'is_duplicate': True,
            'message': f'El número {number} se repite inmediatamente después del último número.'
        }
    
    # Check if appears in last 3 numbers
    if len(recent_numbers) >= 2:
        last_three = recent_numbers[:3]
        if number in last_three:
            position = last_three.index(number) + 1
            return {
                'is_duplicate': True,
                'message': f'El número {number} ya apareció recientemente (posición: {position}).'
            }
    
    # Check frequency in last 5 numbers
    if len(recent_numbers) >= 4:
        last_five = recent_numbers[:5]
        count = last_five.count(number)
        if count >= 2:
            return {
                'is_duplicate': True,
                'message': f'El número {number} ya apareció {count} veces en los últimos {len(last_five)} números.'
            }
    
    return {'is_duplicate': False, 'message': ''}

# ============================================================================
# API ENDPOINTS - ROULETTE NUMBERS
# ============================================================================

@app.route('/api/numeros-recientes', methods=['GET'])
def get_recent_numbers():
    """Get recent roulette numbers"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(max(limit, 1), 100)  # Limit between 1 and 100
        
        numbers = db_manager.get_last_roulette_numbers(limit)
        
        return jsonify({
            'success': True,
            'data': numbers,
            'count': len(numbers)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent numbers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insertar-numero', methods=['POST'])
def insert_single_number():
    """Insert a single roulette number"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        number = data.get('number')
        if number is None:
            return jsonify({'success': False, 'error': 'Number is required'}), 400
        
        if not validate_roulette_number(number):
            return jsonify({'success': False, 'error': 'Invalid roulette number (0-36)'}), 400
        
        # Check for duplicates unless forced
        force = data.get('force', False)
        if not force:
            recent_numbers = db_manager.get_last_roulette_numbers(5)
            recent_values = [n['number'] for n in recent_numbers]
            duplicate_check = check_consecutive_duplicates(number, recent_values)
            
            if duplicate_check['is_duplicate']:
                return jsonify({
                    'success': False,
                    'error': 'duplicate_detected',
                    'message': duplicate_check['message'],
                    'duplicate_number': number,
                    'allow_override': True
                })
        
        # Insert the number
        result = db_manager.insert_roulette_number(number)
        
        if not result:
            return jsonify({'success': False, 'error': 'Failed to insert number'}), 500
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Número {number} insertado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error inserting number: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/insertar-numeros', methods=['POST'])
def insert_multiple_numbers():
    """Insert multiple roulette numbers"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        numbers_text = data.get('numbers', '')
        force = data.get('force', False)
        
        if not numbers_text:
            return jsonify({'success': False, 'error': 'Numbers text is required'}), 400
        
        # Parse numbers
        numbers = parse_numbers_input(numbers_text)
        if not numbers:
            return jsonify({'success': False, 'error': 'No valid numbers found'}), 400
        
        # Check for duplicates unless forced
        if not force:
            recent_numbers = db_manager.get_last_roulette_numbers(5)
            recent_values = [n['number'] for n in recent_numbers]
            
            problematic_numbers = []
            for num in numbers:
                duplicate_check = check_consecutive_duplicates(num, recent_values)
                if duplicate_check['is_duplicate']:
                    problematic_numbers.append({
                        'number': num,
                        'reason': duplicate_check['message']
                    })
            
            if problematic_numbers:
                return jsonify({
                    'success': False,
                    'error': 'duplicates_detected',
                    'message': f'Se detectaron posibles duplicados: {[p["number"] for p in problematic_numbers]}',
                    'duplicate_numbers': problematic_numbers,
                    'allow_override': True
                })
        
        # Insert numbers
        result = db_manager.insert_multiple_numbers(numbers, force=force)
        
        if not result['success']:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Insertados {result["processed_count"]} números correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error inserting multiple numbers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - VOICE RECOGNITION (COMPATIBILITY)
# ============================================================================

@app.route('/reconocer-voz', methods=['POST'])
def process_voice_input():
    """Process voice input (compatibility endpoint)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        text = data.get('text', '')
        force_insert = data.get('force_insert', False)
        
        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        
        # Parse numbers from text
        numbers = parse_numbers_input(text)
        if not numbers:
            return jsonify({'success': False, 'error': 'No valid numbers found in text'}), 400
        
        # Handle single number
        if len(numbers) == 1:
            number = numbers[0]
            
            # Check duplicates unless forced
            if not force_insert:
                recent_numbers = db_manager.get_last_roulette_numbers(5)
                recent_values = [n['number'] for n in recent_numbers]
                duplicate_check = check_consecutive_duplicates(number, recent_values)
                
                if duplicate_check['is_duplicate']:
                    return jsonify({
                        'success': False,
                        'error': 'duplicate_detected',
                        'message': duplicate_check['message'],
                        'duplicate_number': number,
                        'allow_override': True
                    })
            
            # Insert single number
            result = db_manager.insert_roulette_number(number)
            if not result:
                return jsonify({'success': False, 'error': 'Failed to insert number'}), 500
            
            return jsonify({
                'success': True,
                'processed_count': 1,
                'total_input': 1,
                'numbers': [number],
                'last_played': number,
                'individual_entries': [result]
            })
        
        # Handle multiple numbers
        else:
            result = db_manager.insert_multiple_numbers(numbers, force=force_insert)
            if not result['success']:
                return jsonify(result), 500
            
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - STATISTICS
# ============================================================================

@app.route('/api/estadisticas', methods=['GET'])
def get_statistics():
    """Get roulette statistics"""
    try:
        limit = request.args.get('limit', 500, type=int)
        limit = min(max(limit, 50), 1000)  # Limit between 50 and 1000
        
        stats = db_manager.get_roulette_stats(limit)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': 'No data available for statistics'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/secuencias', methods=['GET'])
def get_sequences():
    """Get number sequences for analysis"""
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(max(limit, 20), 500)  # Limit between 20 and 500
        
        # Get recent numbers
        numbers = db_manager.get_last_roulette_numbers(limit)
        
        if not numbers:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
        
        # Transform to sequences format
        sequences = {
            'recent_number_sequence': [n['number'] for n in numbers[:10]],
            'number_sequences': [n['number'] for n in reversed(numbers)],  # Chronological order
            'color_sequences': [n['color'] for n in reversed(numbers)],
            'parity_sequences': [
                'even' if n['number'] != 0 and n['number'] % 2 == 0 
                else 'odd' if n['number'] != 0 
                else 'zero' 
                for n in reversed(numbers)
            ],
            'dozen_sequences': [
                'd1' if 1 <= n['number'] <= 12
                else 'd2' if 13 <= n['number'] <= 24
                else 'd3' if 25 <= n['number'] <= 36
                else 'zero'
                for n in reversed(numbers)
            ],
            'column_sequences': [
                'c1' if n['number'] != 0 and n['number'] % 3 == 1
                else 'c2' if n['number'] != 0 and n['number'] % 3 == 2
                else 'c3' if n['number'] != 0 and n['number'] % 3 == 0
                else 'zero'
                for n in reversed(numbers)
            ],
            'cycles': []
        }
        
        # Create cycles of 5 numbers
        number_seq = sequences['number_sequences']
        color_seq = sequences['color_sequences']
        
        for i in range(0, len(number_seq), 5):
            if i + 5 <= len(number_seq):
                cycle_numbers = number_seq[i:i+5]
                sequences['cycles'].append({
                    'numbers': cycle_numbers,
                    'sum': sum(cycle_numbers),
                    'colors': color_seq[i:i+5]
                })
        
        return jsonify({
            'success': True,
            'data': sequences
        })
        
    except Exception as e:
        logger.error(f"Error getting sequences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - DATABASE MANAGEMENT
# ============================================================================

@app.route('/estado-db', methods=['GET'])
def get_database_status():
    """Get database status"""
    try:
        status = db_manager.get_database_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/purgar-db', methods=['POST'])
def purge_database():
    """Purge old records from database"""
    try:
        data = request.get_json() or {}
        keep_hours = data.get('mantener_horas', 48)
        keep_minimum = data.get('mantener_minimo', 50)
        
        result = db_manager.purge_old_records(keep_hours, keep_minimum)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error purging database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - ML PREDICTIONS (COMPATIBILITY)
# ============================================================================

@app.route('/api/prediccion-basica', methods=['GET'])
def get_basic_prediction():
    """Get basic ML prediction"""
    try:
        # Get recent numbers for prediction
        recent_numbers = db_manager.get_last_roulette_numbers(50)
        if len(recent_numbers) < 10:
            return jsonify({
                'success': False,
                'error': 'Insufficient data for prediction'
            }), 400
        
        # Extract number values
        numbers = [n['number'] for n in recent_numbers]
        
        # Use existing ML logic (simplified)
        # This would integrate with your existing prediction algorithms
        predicted_numbers = generate_basic_prediction(numbers)
        
        return jsonify({
            'success': True,
            'prediction': predicted_numbers,
            'confidence': 0.75,  # Example confidence
            'based_on_numbers': len(numbers)
        })
        
    except Exception as e:
        logger.error(f"Error generating basic prediction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_basic_prediction(numbers: List[int]) -> List[int]:
    """Generate basic prediction based on recent numbers"""
    # This is a simplified version - you would integrate your actual ML logic here
    
    # Analyze frequency
    frequency = {}
    for num in numbers[-20:]:  # Last 20 numbers
        frequency[num] = frequency.get(num, 0) + 1
    
    # Get less frequent numbers (cold numbers strategy)
    all_numbers = list(range(37))  # 0-36
    cold_numbers = []
    
    for num in all_numbers:
        if frequency.get(num, 0) <= 1:  # Appeared once or never
            cold_numbers.append(num)
    
    # If we have enough cold numbers, return a selection
    if len(cold_numbers) >= 20:
        return sorted(cold_numbers[:20])
    
    # Otherwise, return a mix of cold and random numbers
    import random
    remaining_needed = 20 - len(cold_numbers)
    hot_numbers = [num for num in all_numbers if num not in cold_numbers]
    random.shuffle(hot_numbers)
    
    return sorted(cold_numbers + hot_numbers[:remaining_needed])

# ============================================================================
# API ENDPOINTS - ANALYZER STATE
# ============================================================================

@app.route('/api/estado-analizador', methods=['GET'])
def get_analyzer_state():
    """Get analyzer state"""
    try:
        state = db_manager.get_analyzer_state()
        if not state:
            return jsonify({'success': False, 'error': 'Failed to get analyzer state'}), 500
        
        return jsonify({
            'success': True,
            'data': state
        })
        
    except Exception as e:
        logger.error(f"Error getting analyzer state: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/actualizar-analizador', methods=['POST'])
def update_analyzer_state():
    """Update analyzer state"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success = db_manager.update_analyzer_state(data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update analyzer state'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Analyzer state updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating analyzer state: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        status = db_manager.get_database_status()
        db_healthy = status.get('success', False)
        
        # Test Redis connection
        redis_healthy = db_manager.redis_client is not None
        if redis_healthy and db_manager.redis_client:
            try:
                db_manager.redis_client.ping()
            except:
                redis_healthy = False
        
        return jsonify({
            'status': 'healthy' if db_healthy and redis_healthy else 'degraded',
            'database': 'connected' if db_healthy else 'disconnected',
            'redis': 'connected' if redis_healthy else 'disconnected',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ============================================================================
# STATIC FILES (for development)
# ============================================================================

@app.route('/')
def serve_index():
    """Serve index page"""
    return jsonify({
        'message': 'Roulette Analyzer API - PostgreSQL + Redis Version',
        'version': '2.0.0',
        'database': 'PostgreSQL',
        'cache': 'Redis',
        'endpoints': [
            '/health',
            '/api/numeros-recientes',
            '/api/insertar-numero',
            '/api/insertar-numeros',
            '/api/estadisticas',
            '/api/secuencias',
            '/reconocer-voz',
            '/estado-db',
            '/purgar-db'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting Roulette Analyzer API v2.0 on port {port}")
    logger.info(f"📊 Database: PostgreSQL")
    logger.info(f"⚡ Cache: Redis")
    logger.info(f"🔧 Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)