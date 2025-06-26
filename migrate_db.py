#!/usr/bin/env python3
"""
Database migration script for MaintAI
This script initializes the database schema and creates default data
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.main import app, db
from src.models.user import User
from src.models.sensor import Factory, Machine, SensorData, Alert

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")

def create_default_data():
    """Create default data for the application"""
    print("Creating default data...")
    
    with app.app_context():
        # Create default admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@maintai.dz',
                phone_number='+213555000000',
                role='admin',
                factory_id='FACTORY_001',
                language='ar',
                notification_preferences='{"sms": true, "email": true, "push": true}'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("✓ Created default admin user")
        
        # Create default factory
        factory = Factory.query.filter_by(id='FACTORY_001').first()
        if not factory:
            factory = Factory(
                id='FACTORY_001',
                name='مصنع الجزائر الصناعي',
                name_ar='مصنع الجزائر الصناعي',
                location='المنطقة الصناعية، الجزائر',
                wilaya='16',  # Alger
                industry_type='manufacturing',
                manager_name='أحمد بن علي',
                manager_phone='+213555000001',
                plc_type='siemens_s7',
                plc_ip='192.168.1.100',
                plc_port=102
            )
            db.session.add(factory)
            print("✓ Created default factory")
        
        # Create default machines
        machines_data = [
            {
                'id': 'MACHINE_001',
                'name': 'خط الإنتاج الأول',
                'machine_type': 'Production Line',
                'manufacturer': 'Siemens',
                'model': 'S7-1500',
                'production_line': 'Line 1',
                'sensors_config': '{"temperature": {"db_number": 1, "address": 0, "data_type": "real", "unit": "°C"}, "humidity": {"db_number": 1, "address": 4, "data_type": "real", "unit": "%"}, "vibration": {"db_number": 1, "address": 8, "data_type": "real", "unit": "mm/s"}}'
            },
            {
                'id': 'MACHINE_002',
                'name': 'خط الإنتاج الثاني',
                'machine_type': 'Production Line',
                'manufacturer': 'Schneider',
                'model': 'Modicon M580',
                'production_line': 'Line 2',
                'sensors_config': '{"temperature": {"address": 1000, "data_type": "holding_register", "scale_factor": 0.1, "unit": "°C"}, "pressure": {"address": 1001, "data_type": "holding_register", "scale_factor": 0.01, "unit": "bar"}}'
            },
            {
                'id': 'MACHINE_003',
                'name': 'آلة التعبئة والتغليف',
                'machine_type': 'Packaging Machine',
                'manufacturer': 'Siemens',
                'model': 'S7-1200',
                'production_line': 'Packaging',
                'sensors_config': '{"noise": {"db_number": 2, "address": 0, "data_type": "real", "unit": "dB"}, "tension": {"db_number": 2, "address": 4, "data_type": "real", "unit": "V"}}'
            }
        ]
        
        for machine_data in machines_data:
            machine = Machine.query.filter_by(id=machine_data['id']).first()
            if not machine:
                machine = Machine(
                    id=machine_data['id'],
                    name=machine_data['name'],
                    factory_id='FACTORY_001',
                    machine_type=machine_data['machine_type'],
                    manufacturer=machine_data['manufacturer'],
                    model=machine_data['model'],
                    production_line=machine_data['production_line'],
                    sensors_config=machine_data['sensors_config']
                )
                db.session.add(machine)
        
        print("✓ Created default machines")
        
        # Create sample sensor data
        sample_sensors = [
            {'device_id': 'MACHINE_001_temperature', 'sensor_type': 'temperature', 'value': 23.5, 'unit': '°C'},
            {'device_id': 'MACHINE_001_humidity', 'sensor_type': 'humidity', 'value': 45.2, 'unit': '%'},
            {'device_id': 'MACHINE_001_vibration', 'sensor_type': 'vibration', 'value': 1.2, 'unit': 'mm/s'},
            {'device_id': 'MACHINE_002_temperature', 'sensor_type': 'temperature', 'value': 25.1, 'unit': '°C'},
            {'device_id': 'MACHINE_002_pressure', 'sensor_type': 'pressure', 'value': 2.3, 'unit': 'bar'},
            {'device_id': 'MACHINE_003_noise', 'sensor_type': 'noise', 'value': 68.5, 'unit': 'dB'},
            {'device_id': 'MACHINE_003_tension', 'sensor_type': 'tension', 'value': 220.0, 'unit': 'V'}
        ]
        
        for sensor_data in sample_sensors:
            sensor_record = SensorData(
                device_id=sensor_data['device_id'],
                sensor_type=sensor_data['sensor_type'],
                value=sensor_data['value'],
                unit=sensor_data['unit'],
                factory_id='FACTORY_001',
                machine_id=sensor_data['device_id'].split('_')[0] + '_' + sensor_data['device_id'].split('_')[1],
                location='Production Floor',
                shift='morning'
            )
            db.session.add(sensor_record)
        
        print("✓ Created sample sensor data")
        
        # Create sample alert
        sample_alert = Alert.query.filter_by(device_id='MACHINE_001_temperature').first()
        if not sample_alert:
            sample_alert = Alert(
                device_id='MACHINE_001_temperature',
                sensor_type='temperature',
                alert_type='threshold',
                severity='medium',
                message='Temperature reading above normal range',
                message_ar='قراءة درجة الحرارة أعلى من المعدل الطبيعي',
                factory_id='FACTORY_001',
                machine_id='MACHINE_001',
                threshold_value=25.0,
                actual_value=26.5,
                shift='morning'
            )
            db.session.add(sample_alert)
            print("✓ Created sample alert")
        
        db.session.commit()
        print("✓ Default data created successfully")

def main():
    """Main migration function"""
    print("Starting MaintAI database migration...")
    print(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')}")
    
    try:
        create_tables()
        create_default_data()
        print("\n🎉 Database migration completed successfully!")
        print("\nDefault credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@maintai.dz")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

