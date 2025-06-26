from flask import Blueprint, jsonify, request
from src.services.plc_integration import plc_service
from src.services.algerian_market import algerian_service
from src.models.sensor import Factory, Machine, SensorData, db
import json

plc_bp = Blueprint('plc', __name__)

@plc_bp.route('/connect/<factory_id>', methods=['POST'])
def connect_factory_plc(factory_id):
    """Connect to factory PLC systems"""
    try:
        results = plc_service.connect_to_factory_plcs(factory_id)
        
        if results.get(factory_id, False):
            return jsonify({
                'status': 'success',
                'message': f'Connected to PLC for factory {factory_id}',
                'factory_id': factory_id,
                'connection_results': results
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to connect to PLC for factory {factory_id}',
                'factory_id': factory_id,
                'connection_results': results
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/disconnect/<factory_id>', methods=['POST'])
def disconnect_factory_plc(factory_id):
    """Disconnect from factory PLC systems"""
    try:
        plc_service.disconnect_factory_plcs(factory_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Disconnected from PLC for factory {factory_id}',
            'factory_id': factory_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/status', methods=['GET'])
def get_plc_connection_status():
    """Get status of all PLC connections"""
    try:
        status = plc_service.get_connection_status()
        
        return jsonify({
            'status': 'success',
            'connections': status,
            'total_connections': len(status)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/test/<factory_id>', methods=['POST'])
def test_plc_communication(factory_id):
    """Test PLC communication for a factory"""
    try:
        test_result = plc_service.test_plc_communication(factory_id)
        
        return jsonify({
            'status': 'success',
            'factory_id': factory_id,
            'test_result': test_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/read-sensors/<factory_id>/<machine_id>', methods=['POST'])
def read_sensors_from_plc(factory_id, machine_id):
    """Read sensor data from PLC for a specific machine"""
    try:
        # Get machine configuration
        machine = Machine.query.get(machine_id)
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        if machine.factory_id != factory_id:
            return jsonify({'error': 'Machine does not belong to specified factory'}), 400
        
        # Parse sensor configuration
        sensor_config = {}
        if machine.sensors_config:
            try:
                sensor_config = json.loads(machine.sensors_config)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid sensor configuration'}), 400
        
        if not sensor_config:
            return jsonify({'error': 'No sensor configuration found for machine'}), 400
        
        # Read sensor data from PLC
        sensor_data = plc_service.read_sensor_data_from_plc(factory_id, machine_id, sensor_config)
        
        if sensor_data:
            # Store sensor data in database
            stored_records = []
            for sensor_type, data in sensor_data.items():
                sensor_record = SensorData(
                    device_id=f"{machine_id}_{sensor_type}",
                    sensor_type=sensor_type,
                    value=data['value'],
                    unit=data['unit'],
                    factory_id=factory_id,
                    machine_id=machine_id,
                    location=machine.production_line,
                    shift=algerian_service.get_current_shift()['shift']
                )
                db.session.add(sensor_record)
                stored_records.append(sensor_record.to_dict())
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Read {len(sensor_data)} sensor values from PLC',
                'factory_id': factory_id,
                'machine_id': machine_id,
                'sensor_data': sensor_data,
                'stored_records': stored_records
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to read sensor data from PLC',
                'factory_id': factory_id,
                'machine_id': machine_id
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/write-alert/<factory_id>', methods=['POST'])
def write_alert_to_plc(factory_id):
    """Write alert information to PLC"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['alert_type', 'severity', 'machine_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Write alert to PLC
        success = plc_service.write_alert_to_plc(factory_id, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Alert written to PLC successfully',
                'factory_id': factory_id,
                'alert_data': data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to write alert to PLC',
                'factory_id': factory_id
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/configure-machine/<machine_id>', methods=['POST'])
def configure_machine_sensors(machine_id):
    """Configure sensor mapping for a machine"""
    try:
        data = request.json
        
        machine = Machine.query.get(machine_id)
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        # Validate sensor configuration
        sensor_config = data.get('sensor_config', {})
        
        # Example configuration validation for Siemens
        if machine.factory_id:
            factory = Factory.query.get(machine.factory_id)
            if factory and factory.plc_type and factory.plc_type.startswith('siemens'):
                # Validate Siemens configuration
                for sensor_type, config in sensor_config.items():
                    if 'db_number' not in config or 'address' not in config:
                        return jsonify({
                            'error': f'Invalid Siemens configuration for sensor {sensor_type}. Missing db_number or address.'
                        }), 400
            
            elif factory and factory.plc_type and factory.plc_type.startswith('schneider'):
                # Validate Schneider configuration
                for sensor_type, config in sensor_config.items():
                    if 'address' not in config:
                        return jsonify({
                            'error': f'Invalid Schneider configuration for sensor {sensor_type}. Missing address.'
                        }), 400
        
        # Update machine configuration
        machine.sensors_config = json.dumps(sensor_config)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Machine sensor configuration updated',
            'machine_id': machine_id,
            'sensor_config': sensor_config
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/siemens/tia-portal-export', methods=['POST'])
def import_tia_portal_configuration():
    """Import configuration from TIA Portal export"""
    try:
        data = request.json
        factory_id = data.get('factory_id')
        tia_export_data = data.get('tia_export_data', {})
        
        if not factory_id:
            return jsonify({'error': 'Missing factory_id'}), 400
        
        factory = Factory.query.get(factory_id)
        if not factory:
            return jsonify({'error': 'Factory not found'}), 404
        
        # Parse TIA Portal export data
        imported_machines = []
        
        # Example TIA Portal data structure
        for plc_data in tia_export_data.get('plcs', []):
            plc_name = plc_data.get('name', 'Unknown PLC')
            
            for db_data in plc_data.get('data_blocks', []):
                db_number = db_data.get('number')
                db_name = db_data.get('name', f'DB{db_number}')
                
                # Create or update machine based on DB
                machine_id = f"{factory_id}_{plc_name}_{db_name}"
                machine = Machine.query.get(machine_id)
                
                if not machine:
                    machine = Machine(
                        id=machine_id,
                        name=db_name,
                        factory_id=factory_id,
                        machine_type='PLC_Controlled',
                        manufacturer='Siemens'
                    )
                    db.session.add(machine)
                
                # Configure sensors based on DB variables
                sensor_config = {}
                for variable in db_data.get('variables', []):
                    var_name = variable.get('name', '')
                    var_address = variable.get('address', 0)
                    var_type = variable.get('type', 'REAL')
                    
                    # Map variable names to sensor types
                    sensor_type = self._map_variable_to_sensor_type(var_name)
                    if sensor_type:
                        sensor_config[sensor_type] = {
                            'db_number': db_number,
                            'address': var_address,
                            'data_type': var_type.lower(),
                            'unit': self._get_sensor_unit(sensor_type),
                            'variable_name': var_name
                        }
                
                machine.sensors_config = json.dumps(sensor_config)
                imported_machines.append({
                    'machine_id': machine_id,
                    'name': db_name,
                    'sensors_configured': len(sensor_config)
                })
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Imported configuration for {len(imported_machines)} machines',
            'factory_id': factory_id,
            'imported_machines': imported_machines
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/schneider/unity-export', methods=['POST'])
def import_unity_configuration():
    """Import configuration from Schneider Unity Pro export"""
    try:
        data = request.json
        factory_id = data.get('factory_id')
        unity_export_data = data.get('unity_export_data', {})
        
        if not factory_id:
            return jsonify({'error': 'Missing factory_id'}), 400
        
        factory = Factory.query.get(factory_id)
        if not factory:
            return jsonify({'error': 'Factory not found'}), 404
        
        # Parse Unity Pro export data
        imported_machines = []
        
        # Example Unity Pro data structure
        for module_data in unity_export_data.get('modules', []):
            module_name = module_data.get('name', 'Unknown Module')
            
            # Create or update machine based on module
            machine_id = f"{factory_id}_{module_name}"
            machine = Machine.query.get(machine_id)
            
            if not machine:
                machine = Machine(
                    id=machine_id,
                    name=module_name,
                    factory_id=factory_id,
                    machine_type='PLC_Controlled',
                    manufacturer='Schneider'
                )
                db.session.add(machine)
            
            # Configure sensors based on module variables
            sensor_config = {}
            for variable in module_data.get('variables', []):
                var_name = variable.get('name', '')
                var_address = variable.get('address', 0)
                var_type = variable.get('type', 'INT')
                
                # Map variable names to sensor types
                sensor_type = self._map_variable_to_sensor_type(var_name)
                if sensor_type:
                    sensor_config[sensor_type] = {
                        'address': var_address,
                        'data_type': 'holding_register',
                        'scale_factor': variable.get('scale_factor', 1.0),
                        'unit': self._get_sensor_unit(sensor_type),
                        'variable_name': var_name
                    }
            
            machine.sensors_config = json.dumps(sensor_config)
            imported_machines.append({
                'machine_id': machine_id,
                'name': module_name,
                'sensors_configured': len(sensor_config)
            })
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Imported configuration for {len(imported_machines)} machines',
            'factory_id': factory_id,
            'imported_machines': imported_machines
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/algerian-compliance/<factory_id>', methods=['GET'])
def get_algerian_compliance_info(factory_id):
    """Get Algerian compliance information for factory"""
    try:
        compliance_info = algerian_service.get_factory_compliance_info(factory_id)
        
        return jsonify({
            'status': 'success',
            'factory_id': factory_id,
            'compliance_info': compliance_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plc_bp.route('/maintenance-report/<factory_id>', methods=['POST'])
def generate_maintenance_report(factory_id):
    """Generate maintenance report for Algerian authorities"""
    try:
        data = request.json
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Missing start_date or end_date'}), 400
        
        from datetime import datetime
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        
        report = algerian_service.generate_maintenance_report_algeria(factory_id, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'report': report
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _map_variable_to_sensor_type(variable_name: str) -> str:
    """Map PLC variable name to sensor type"""
    variable_name_lower = variable_name.lower()
    
    if any(keyword in variable_name_lower for keyword in ['temp', 'temperature', 'درجة']):
        return 'temperature'
    elif any(keyword in variable_name_lower for keyword in ['humid', 'humidity', 'رطوبة']):
        return 'humidity'
    elif any(keyword in variable_name_lower for keyword in ['noise', 'sound', 'ضوضاء']):
        return 'noise'
    elif any(keyword in variable_name_lower for keyword in ['volt', 'tension', 'توتر']):
        return 'tension'
    elif any(keyword in variable_name_lower for keyword in ['vibr', 'vibration', 'اهتزاز']):
        return 'vibration'
    elif any(keyword in variable_name_lower for keyword in ['press', 'pressure', 'ضغط']):
        return 'pressure'
    elif any(keyword in variable_name_lower for keyword in ['flow', 'rate', 'تدفق']):
        return 'flow_rate'
    
    return None

def _get_sensor_unit(sensor_type: str) -> str:
    """Get default unit for sensor type"""
    units = {
        'temperature': '°C',
        'humidity': '%',
        'noise': 'dB',
        'tension': 'V',
        'vibration': 'mm/s',
        'pressure': 'bar',
        'flow_rate': 'L/min'
    }
    return units.get(sensor_type, '')

