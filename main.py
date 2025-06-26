import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

from src.models.user import db
from src.routes.user import user_bp
from src.routes.sensor import sensor_bp
from src.routes.ml import ml_bp
from src.routes.notification import notification_bp
from src.routes.plc import plc_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'maintai-predictive-failure-system-2025')

# Enable CORS for all routes
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    CORS(app, origins=cors_origins.split(','))

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(sensor_bp, url_prefix='/api')
app.register_blueprint(ml_bp, url_prefix='/api')
app.register_blueprint(notification_bp, url_prefix='/api')
app.register_blueprint(plc_bp, url_prefix='/api/plc')

# Database configuration - PostgreSQL for production, SQLite for development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production: Use PostgreSQL from Render
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}

db.init_app(app)

# Health check endpoints
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'service': 'MaintAI Predictive Maintenance System'
    })

@app.route('/health/db')
def health_check_db():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# API documentation endpoint
@app.route('/api/docs')
def api_docs():
    return jsonify({
        'title': 'MaintAI API Documentation',
        'version': '1.0.0',
        'description': 'Predictive Maintenance System for Algerian Industrial Market',
        'base_url': '/api',
        'endpoints': {
            'health': {
                'GET /health': 'Application health check',
                'GET /health/db': 'Database health check'
            },
            'authentication': {
                'POST /api/users/login': 'User login',
                'POST /api/users/logout': 'User logout',
                'GET /api/users/profile': 'Get user profile'
            },
            'sensor_data': {
                'GET /api/sensor-data/latest': 'Get latest sensor readings',
                'POST /api/sensor-data': 'Submit sensor data',
                'POST /api/sensor-data/batch': 'Submit batch sensor data',
                'GET /api/sensor-data/{device_id}': 'Get device sensor history'
            },
            'alerts': {
                'GET /api/alerts': 'Get alerts with filtering',
                'POST /api/alerts/{id}/acknowledge': 'Acknowledge alert',
                'POST /api/alerts/{id}/resolve': 'Resolve alert'
            },
            'machine_learning': {
                'POST /api/analyze': 'Analyze sensor data for anomalies',
                'POST /api/train-models': 'Train prediction models',
                'GET /api/model-status': 'Get model training status',
                'POST /api/predict-batch': 'Batch prediction analysis'
            },
            'plc_integration': {
                'POST /api/plc/connect/{factory_id}': 'Connect to factory PLC',
                'POST /api/plc/read-sensors/{factory_id}/{machine_id}': 'Read PLC sensors',
                'POST /api/plc/siemens/tia-portal-export': 'Import TIA Portal config',
                'POST /api/plc/schneider/unity-export': 'Import Unity Pro config'
            },
            'notifications': {
                'POST /api/notifications/send-alert/{alert_id}': 'Send alert notification',
                'POST /api/notifications/test/{user_id}': 'Test notifications',
                'GET /api/notifications/history': 'Get notification history'
            },
            'dashboard': {
                'GET /api/dashboard/summary': 'Get dashboard summary',
                'GET /api/machines': 'Get machines list',
                'GET /api/factories': 'Get factories list'
            }
        },
        'features': [
            'Real-time sensor monitoring',
            'Predictive failure analysis',
            'Multi-language support (Arabic, French, English)',
            'Siemens S7 PLC integration',
            'Schneider Modicon PLC integration',
            'SMS and email notifications',
            'Algerian market customization',
            'Industrial compliance reporting'
        ]
    })

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
