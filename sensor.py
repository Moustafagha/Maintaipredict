from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.sensor import SensorData, Alert, Machine, Factory, db
from src.services.ml_service import ml_service
import json

sensor_bp = Blueprint('sensor', __name__)

@sensor_bp.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from IoT devices"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['device_id', 'sensor_type', 'value', 'unit', 'factory_id', 'machine_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create sensor data record
        sensor_data = SensorData(
            device_id=data['device_id'],
            sensor_type=data['sensor_type'],
            value=float(data['value']),
            unit=data['unit'],
            location=data.get('location'),
            factory_id=data['factory_id'],
            machine_id=data['machine_id'],
            shift=data.get('shift'),
            operator_id=data.get('operator_id'),
            production_line=data.get('production_line'),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(sensor_data)
        db.session.commit()
        
        # Perform real-time analysis
        analysis_result = analyze_sensor_data(sensor_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Sensor data received and analyzed',
            'data_id': sensor_data.id,
            'analysis': analysis_result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/sensor-data/<device_id>', methods=['GET'])
def get_sensor_data(device_id):
    """Get sensor data for a specific device"""
    try:
        # Get query parameters
        sensor_type = request.args.get('sensor_type')
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 1000))
        
        # Build query
        query = SensorData.query.filter(SensorData.device_id == device_id)
        
        if sensor_type:
            query = query.filter(SensorData.sensor_type == sensor_type)
        
        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SensorData.timestamp >= cutoff_time)
        
        # Order and limit
        data = query.order_by(SensorData.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'data': [d.to_dict() for d in data],
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/sensor-data/batch', methods=['POST'])
def receive_batch_sensor_data():
    """Receive batch sensor data from multiple devices"""
    try:
        data = request.json
        
        if not isinstance(data, list):
            return jsonify({'error': 'Expected array of sensor data'}), 400
        
        created_records = []
        analysis_results = []
        
        for item in data:
            # Validate required fields
            required_fields = ['device_id', 'sensor_type', 'value', 'unit', 'factory_id', 'machine_id']
            for field in required_fields:
                if field not in item:
                    continue  # Skip invalid records
            
            # Create sensor data record
            sensor_data = SensorData(
                device_id=item['device_id'],
                sensor_type=item['sensor_type'],
                value=float(item['value']),
                unit=item['unit'],
                location=item.get('location'),
                factory_id=item['factory_id'],
                machine_id=item['machine_id'],
                shift=item.get('shift'),
                operator_id=item.get('operator_id'),
                production_line=item.get('production_line'),
                timestamp=datetime.fromisoformat(item['timestamp']) if 'timestamp' in item else datetime.utcnow()
            )
            
            db.session.add(sensor_data)
            created_records.append(sensor_data)
        
        db.session.commit()
        
        # Analyze each record
        for sensor_data in created_records:
            analysis_result = analyze_sensor_data(sensor_data)
            analysis_results.append(analysis_result)
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(created_records)} sensor data records',
            'processed_count': len(created_records),
            'analysis_results': analysis_results
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with filtering options"""
    try:
        # Get query parameters
        factory_id = request.args.get('factory_id')
        machine_id = request.args.get('machine_id')
        severity = request.args.get('severity')
        acknowledged = request.args.get('acknowledged')
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = Alert.query
        
        if factory_id:
            query = query.filter(Alert.factory_id == factory_id)
        
        if machine_id:
            query = query.filter(Alert.machine_id == machine_id)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        if acknowledged is not None:
            ack_bool = acknowledged.lower() == 'true'
            query = query.filter(Alert.acknowledged == ack_bool)
        
        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(Alert.timestamp >= cutoff_time)
        
        # Order and limit
        alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.json
        user_id = data.get('user_id', 'system')
        
        alert = Alert.query.get_or_404(alert_id)
        
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert acknowledged',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        data = request.json
        user_id = data.get('user_id', 'system')
        
        alert = Alert.query.get_or_404(alert_id)
        
        alert.resolved = True
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert resolved',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/machines', methods=['GET'])
def get_machines():
    """Get machines with their current status"""
    try:
        factory_id = request.args.get('factory_id')
        
        query = Machine.query
        if factory_id:
            query = query.filter(Machine.factory_id == factory_id)
        
        machines = query.all()
        
        # Get latest sensor data for each machine
        machines_data = []
        for machine in machines:
            machine_dict = machine.to_dict()
            
            # Get latest sensor readings
            latest_sensors = {}
            sensor_types = ['temperature', 'humidity', 'noise', 'tension', 'vibration']
            
            for sensor_type in sensor_types:
                latest_data = SensorData.query.filter(
                    SensorData.machine_id == machine.id,
                    SensorData.sensor_type == sensor_type
                ).order_by(SensorData.timestamp.desc()).first()
                
                if latest_data:
                    latest_sensors[sensor_type] = {
                        'value': latest_data.value,
                        'unit': latest_data.unit,
                        'timestamp': latest_data.timestamp.isoformat()
                    }
            
            machine_dict['latest_sensors'] = latest_sensors
            
            # Get active alerts count
            active_alerts = Alert.query.filter(
                Alert.machine_id == machine.id,
                Alert.resolved == False
            ).count()
            
            machine_dict['active_alerts'] = active_alerts
            
            machines_data.append(machine_dict)
        
        return jsonify({
            'status': 'success',
            'machines': machines_data,
            'count': len(machines_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/factories', methods=['GET'])
def get_factories():
    """Get all factories"""
    try:
        factories = Factory.query.all()
        
        return jsonify({
            'status': 'success',
            'factories': [factory.to_dict() for factory in factories],
            'count': len(factories)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sensor_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary data"""
    try:
        factory_id = request.args.get('factory_id')
        hours = int(request.args.get('hours', 24))
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build base queries
        sensor_query = SensorData.query.filter(SensorData.timestamp >= cutoff_time)
        alert_query = Alert.query.filter(Alert.timestamp >= cutoff_time)
        
        if factory_id:
            sensor_query = sensor_query.filter(SensorData.factory_id == factory_id)
            alert_query = alert_query.filter(Alert.factory_id == factory_id)
        
        # Get summary statistics
        total_sensors = sensor_query.count()
        total_alerts = alert_query.count()
        critical_alerts = alert_query.filter(Alert.severity == 'critical').count()
        unresolved_alerts = alert_query.filter(Alert.resolved == False).count()
        
        # Get sensor type distribution
        sensor_types = db.session.query(
            SensorData.sensor_type,
            db.func.count(SensorData.id).label('count')
        ).filter(SensorData.timestamp >= cutoff_time)
        
        if factory_id:
            sensor_types = sensor_types.filter(SensorData.factory_id == factory_id)
        
        sensor_types = sensor_types.group_by(SensorData.sensor_type).all()
        
        # Get alert severity distribution
        alert_severity = db.session.query(
            Alert.severity,
            db.func.count(Alert.id).label('count')
        ).filter(Alert.timestamp >= cutoff_time)
        
        if factory_id:
            alert_severity = alert_severity.filter(Alert.factory_id == factory_id)
        
        alert_severity = alert_severity.group_by(Alert.severity).all()
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total_sensors': total_sensors,
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'unresolved_alerts': unresolved_alerts,
                'sensor_types': [{'type': st[0], 'count': st[1]} for st in sensor_types],
                'alert_severity': [{'severity': as_[0], 'count': as_[1]} for as_ in alert_severity],
                'time_range_hours': hours
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_sensor_data(sensor_data):
    """Analyze sensor data for anomalies and predictions"""
    try:
        analysis_result = {
            'anomaly_detected': False,
            'anomaly_confidence': 0.0,
            'predicted_failure_hours': 0,
            'prediction_confidence': 0.0,
            'alerts_created': []
        }
        
        # Prepare data for ML analysis
        current_data = {
            'value': sensor_data.value,
            'factory_id': sensor_data.factory_id,
            'machine_id': sensor_data.machine_id
        }
        
        # Anomaly detection
        is_anomaly, anomaly_confidence, anomaly_message = ml_service.detect_anomaly(
            sensor_data.device_id,
            sensor_data.sensor_type,
            current_data
        )
        
        analysis_result['anomaly_detected'] = is_anomaly
        analysis_result['anomaly_confidence'] = anomaly_confidence
        
        # Create anomaly alert if detected
        if is_anomaly and anomaly_confidence > 0.7:
            severity = 'critical' if anomaly_confidence > 0.9 else 'high'
            message = f"Anomaly detected in {sensor_data.sensor_type} sensor: {sensor_data.value} {sensor_data.unit}"
            
            alert = ml_service.create_alert(
                device_id=sensor_data.device_id,
                sensor_type=sensor_data.sensor_type,
                alert_type='anomaly',
                severity=severity,
                message=message,
                confidence_score=anomaly_confidence,
                factory_id=sensor_data.factory_id,
                machine_id=sensor_data.machine_id
            )
            
            analysis_result['alerts_created'].append(alert.id)
        
        # Failure prediction
        predicted_hours, prediction_confidence, prediction_message = ml_service.predict_failure(
            sensor_data.device_id,
            sensor_data.sensor_type,
            current_data
        )
        
        analysis_result['predicted_failure_hours'] = predicted_hours
        analysis_result['prediction_confidence'] = prediction_confidence
        
        # Create prediction alert if failure is imminent
        if predicted_hours < 48 and prediction_confidence > 0.6:  # Less than 48 hours
            severity = 'critical' if predicted_hours < 12 else 'high'
            predicted_time = datetime.utcnow() + timedelta(hours=predicted_hours)
            message = f"Predicted failure in {predicted_hours:.1f} hours for {sensor_data.sensor_type} sensor"
            
            alert = ml_service.create_alert(
                device_id=sensor_data.device_id,
                sensor_type=sensor_data.sensor_type,
                alert_type='prediction',
                severity=severity,
                message=message,
                predicted_failure_time=predicted_time,
                confidence_score=prediction_confidence,
                factory_id=sensor_data.factory_id,
                machine_id=sensor_data.machine_id
            )
            
            analysis_result['alerts_created'].append(alert.id)
        
        return analysis_result
        
    except Exception as e:
        return {
            'error': str(e),
            'anomaly_detected': False,
            'anomaly_confidence': 0.0,
            'predicted_failure_hours': 0,
            'prediction_confidence': 0.0,
            'alerts_created': []
        }

