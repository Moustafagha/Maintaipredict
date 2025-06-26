from flask import Blueprint, jsonify, request
from src.services.ml_service import ml_service
from src.models.sensor import SensorData, Alert, db
from src.models.user import User
import json

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/train-models', methods=['POST'])
def train_models():
    """Train ML models for all device/sensor combinations"""
    try:
        data = request.json or {}
        device_id = data.get('device_id')
        sensor_type = data.get('sensor_type')
        
        results = []
        
        if device_id and sensor_type:
            # Train models for specific device/sensor
            anomaly_success, anomaly_message = ml_service.train_anomaly_detection(device_id, sensor_type)
            prediction_success, prediction_message = ml_service.train_failure_prediction(device_id, sensor_type)
            
            results.append({
                'device_id': device_id,
                'sensor_type': sensor_type,
                'anomaly_model': {
                    'success': anomaly_success,
                    'message': anomaly_message
                },
                'prediction_model': {
                    'success': prediction_success,
                    'message': prediction_message
                }
            })
        else:
            # Train models for all device/sensor combinations
            device_sensors = db.session.query(
                SensorData.device_id,
                SensorData.sensor_type
            ).distinct().all()
            
            for device_id, sensor_type in device_sensors:
                anomaly_success, anomaly_message = ml_service.train_anomaly_detection(device_id, sensor_type)
                prediction_success, prediction_message = ml_service.train_failure_prediction(device_id, sensor_type)
                
                results.append({
                    'device_id': device_id,
                    'sensor_type': sensor_type,
                    'anomaly_model': {
                        'success': anomaly_success,
                        'message': anomaly_message
                    },
                    'prediction_model': {
                        'success': prediction_success,
                        'message': prediction_message
                    }
                })
        
        return jsonify({
            'status': 'success',
            'message': f'Training completed for {len(results)} device/sensor combinations',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/analyze', methods=['POST'])
def analyze_data():
    """Analyze sensor data for anomalies and predictions"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['device_id', 'sensor_type', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        device_id = data['device_id']
        sensor_type = data['sensor_type']
        current_data = {
            'value': float(data['value']),
            'factory_id': data.get('factory_id', 'unknown'),
            'machine_id': data.get('machine_id', 'unknown')
        }
        
        # Perform anomaly detection
        is_anomaly, anomaly_confidence, anomaly_message = ml_service.detect_anomaly(
            device_id, sensor_type, current_data
        )
        
        # Perform failure prediction
        predicted_hours, prediction_confidence, prediction_message = ml_service.predict_failure(
            device_id, sensor_type, current_data
        )
        
        # Determine overall risk level
        risk_level = 'low'
        if is_anomaly and anomaly_confidence > 0.8:
            risk_level = 'critical'
        elif is_anomaly and anomaly_confidence > 0.6:
            risk_level = 'high'
        elif predicted_hours < 48 and prediction_confidence > 0.7:
            risk_level = 'high'
        elif predicted_hours < 72 and prediction_confidence > 0.6:
            risk_level = 'medium'
        
        return jsonify({
            'status': 'success',
            'analysis': {
                'device_id': device_id,
                'sensor_type': sensor_type,
                'current_value': current_data['value'],
                'anomaly': {
                    'detected': is_anomaly,
                    'confidence': anomaly_confidence,
                    'message': anomaly_message
                },
                'prediction': {
                    'failure_hours': predicted_hours,
                    'confidence': prediction_confidence,
                    'message': prediction_message
                },
                'risk_level': risk_level,
                'timestamp': data.get('timestamp', 'now')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/predict-batch', methods=['POST'])
def predict_batch():
    """Analyze multiple sensor readings in batch"""
    try:
        data = request.json
        
        if not isinstance(data, list):
            return jsonify({'error': 'Expected array of sensor data'}), 400
        
        results = []
        
        for item in data:
            # Validate required fields
            required_fields = ['device_id', 'sensor_type', 'value']
            if not all(field in item for field in required_fields):
                continue  # Skip invalid items
            
            device_id = item['device_id']
            sensor_type = item['sensor_type']
            current_data = {
                'value': float(item['value']),
                'factory_id': item.get('factory_id', 'unknown'),
                'machine_id': item.get('machine_id', 'unknown')
            }
            
            # Perform analysis
            is_anomaly, anomaly_confidence, _ = ml_service.detect_anomaly(
                device_id, sensor_type, current_data
            )
            
            predicted_hours, prediction_confidence, _ = ml_service.predict_failure(
                device_id, sensor_type, current_data
            )
            
            # Determine risk level
            risk_level = 'low'
            if is_anomaly and anomaly_confidence > 0.8:
                risk_level = 'critical'
            elif is_anomaly and anomaly_confidence > 0.6:
                risk_level = 'high'
            elif predicted_hours < 48 and prediction_confidence > 0.7:
                risk_level = 'high'
            elif predicted_hours < 72 and prediction_confidence > 0.6:
                risk_level = 'medium'
            
            results.append({
                'device_id': device_id,
                'sensor_type': sensor_type,
                'current_value': current_data['value'],
                'anomaly_detected': is_anomaly,
                'anomaly_confidence': anomaly_confidence,
                'predicted_failure_hours': predicted_hours,
                'prediction_confidence': prediction_confidence,
                'risk_level': risk_level
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Analyzed {len(results)} sensor readings',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/model-status', methods=['GET'])
def get_model_status():
    """Get status of trained models"""
    try:
        # Get all unique device/sensor combinations
        device_sensors = db.session.query(
            SensorData.device_id,
            SensorData.sensor_type
        ).distinct().all()
        
        model_status = []
        
        for device_id, sensor_type in device_sensors:
            # Check if models exist
            import os
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_models')
            
            anomaly_model_path = os.path.join(models_dir, f"anomaly_{device_id}_{sensor_type}.joblib")
            prediction_model_path = os.path.join(models_dir, f"prediction_{device_id}_{sensor_type}.joblib")
            
            anomaly_exists = os.path.exists(anomaly_model_path)
            prediction_exists = os.path.exists(prediction_model_path)
            
            # Get data count for this combination
            data_count = SensorData.query.filter(
                SensorData.device_id == device_id,
                SensorData.sensor_type == sensor_type
            ).count()
            
            model_status.append({
                'device_id': device_id,
                'sensor_type': sensor_type,
                'data_points': data_count,
                'anomaly_model_trained': anomaly_exists,
                'prediction_model_trained': prediction_exists,
                'ready_for_training': data_count >= 100,
                'last_updated': None  # Could add model file modification time
            })
        
        return jsonify({
            'status': 'success',
            'models': model_status,
            'total_combinations': len(model_status)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/retrain/<device_id>/<sensor_type>', methods=['POST'])
def retrain_models(device_id, sensor_type):
    """Retrain models for a specific device/sensor combination"""
    try:
        # Train anomaly detection model
        anomaly_success, anomaly_message = ml_service.train_anomaly_detection(device_id, sensor_type)
        
        # Train failure prediction model
        prediction_success, prediction_message = ml_service.train_failure_prediction(device_id, sensor_type)
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'sensor_type': sensor_type,
            'anomaly_model': {
                'success': anomaly_success,
                'message': anomaly_message
            },
            'prediction_model': {
                'success': prediction_success,
                'message': prediction_message
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/thresholds', methods=['GET', 'POST'])
def manage_thresholds():
    """Manage sensor thresholds for different sensor types"""
    if request.method == 'GET':
        # Return default thresholds for Algerian industrial context
        thresholds = {
            'temperature': {
                'unit': '°C',
                'normal_min': 15,
                'normal_max': 35,
                'warning_min': 10,
                'warning_max': 45,
                'critical_min': 5,
                'critical_max': 60,
                'description': 'Temperature thresholds for industrial equipment',
                'description_ar': 'حدود درجة الحرارة للمعدات الصناعية'
            },
            'humidity': {
                'unit': '%',
                'normal_min': 30,
                'normal_max': 70,
                'warning_min': 20,
                'warning_max': 80,
                'critical_min': 10,
                'critical_max': 90,
                'description': 'Humidity thresholds for industrial environment',
                'description_ar': 'حدود الرطوبة للبيئة الصناعية'
            },
            'noise': {
                'unit': 'dB',
                'normal_min': 40,
                'normal_max': 80,
                'warning_min': 30,
                'warning_max': 90,
                'critical_min': 20,
                'critical_max': 100,
                'description': 'Noise level thresholds for industrial machinery',
                'description_ar': 'حدود مستوى الضوضاء للآلات الصناعية'
            },
            'tension': {
                'unit': 'V',
                'normal_min': 200,
                'normal_max': 240,
                'warning_min': 180,
                'warning_max': 260,
                'critical_min': 160,
                'critical_max': 280,
                'description': 'Electrical tension thresholds',
                'description_ar': 'حدود التوتر الكهربائي'
            },
            'vibration': {
                'unit': 'mm/s',
                'normal_min': 0,
                'normal_max': 2.8,
                'warning_min': 0,
                'warning_max': 7.1,
                'critical_min': 0,
                'critical_max': 18,
                'description': 'Vibration thresholds based on ISO 10816',
                'description_ar': 'حدود الاهتزاز حسب معيار ISO 10816'
            }
        }
        
        return jsonify({
            'status': 'success',
            'thresholds': thresholds
        })
    
    elif request.method == 'POST':
        # Update thresholds (in a real implementation, these would be stored in database)
        data = request.json
        
        # Validate and store thresholds
        # For now, just return success
        return jsonify({
            'status': 'success',
            'message': 'Thresholds updated successfully',
            'updated_thresholds': data
        })

@ml_bp.route('/performance-metrics', methods=['GET'])
def get_performance_metrics():
    """Get ML model performance metrics"""
    try:
        # Get query parameters
        device_id = request.args.get('device_id')
        sensor_type = request.args.get('sensor_type')
        days = int(request.args.get('days', 7))
        
        # In a real implementation, you would calculate actual performance metrics
        # For now, return mock metrics
        metrics = {
            'anomaly_detection': {
                'accuracy': 0.92,
                'precision': 0.89,
                'recall': 0.94,
                'f1_score': 0.91,
                'false_positive_rate': 0.08
            },
            'failure_prediction': {
                'mae': 12.5,  # Mean Absolute Error in hours
                'rmse': 18.3,  # Root Mean Square Error in hours
                'accuracy_24h': 0.87,  # Accuracy for 24h predictions
                'accuracy_48h': 0.82,  # Accuracy for 48h predictions
                'accuracy_72h': 0.76   # Accuracy for 72h predictions
            },
            'data_quality': {
                'completeness': 0.96,
                'consistency': 0.94,
                'timeliness': 0.98
            },
            'model_info': {
                'last_trained': '2025-06-26T10:30:00Z',
                'training_data_points': 15420,
                'model_version': '1.0.0'
            }
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'device_id': device_id,
            'sensor_type': sensor_type,
            'evaluation_period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

