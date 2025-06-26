# MaintAI - نظام الصيانة التنبؤية

## Predictive Maintenance System for Algerian Industrial Market

MaintAI is a comprehensive predictive maintenance system designed specifically for the Algerian industrial market, featuring integration with Siemens and Schneider PLC systems, multi-language support (Arabic, French, English), and compliance with Algerian industrial regulations.

## 🌟 Features

### Core Functionality
- **Real-time Sensor Monitoring**: Temperature, humidity, noise, tension, vibration, pressure monitoring
- **Predictive Analytics**: Machine learning-based failure prediction
- **Alert Management**: Multi-level alert system with SMS, email, and IoT notifications
- **Dashboard**: Responsive web dashboard with real-time data visualization
- **Multi-language Support**: Arabic, French, and English interfaces

### Industrial Integration
- **Siemens Integration**: S7 PLC communication, TIA Portal configuration import
- **Schneider Integration**: Modicon PLC support, Unity Pro configuration import
- **SCADA Compatibility**: Integration with existing SCADA systems
- **IoT Device Support**: Communication with industrial IoT devices

### Algerian Market Specific
- **Wilaya Support**: All 58 Algerian provinces supported
- **Working Hours**: Algerian work schedule and shift management
- **Holiday Calendar**: Islamic and national holidays consideration
- **Compliance**: Algerian industrial regulations and standards
- **Local Suppliers**: Integration with local equipment suppliers

## 🚀 Quick Start with Render

### Prerequisites
- Render account
- GitHub repository
- Basic understanding of Flask and PostgreSQL

### Deployment Steps

#### Step 1: Prepare Your GitHub Repository
1. Fork or clone this repository to your GitHub account
2. Ensure all files are committed and pushed to your repository

#### Step 2: Create PostgreSQL Database on Render
1. Log in to your Render dashboard
2. Click "New" → "PostgreSQL"
3. Configure your database:
   - Name: `maintai-postgres`
   - Database Name: `maintai_db`
   - User: `maintai_user`
   - Plan: Choose based on your needs (Starter for testing)
4. Click "Create Database"
5. Copy the **Internal Database URL** from the database info page

#### Step 3: Deploy Web Service
1. In Render dashboard, click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `maintai-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT src.main:app`

#### Step 4: Configure Environment Variables
Add these environment variables in Render:

**Required Variables:**
```
DATABASE_URL=<your-postgres-internal-url>
SECRET_KEY=<generate-random-secret-key>
FLASK_ENV=production
FLASK_APP=src.main:app
```

**Optional Variables (for full functionality):**
```
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_PHONE_NUMBER=<your-twilio-phone>
EMAIL_USERNAME=<your-email>
EMAIL_PASSWORD=<your-email-password>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
CORS_ORIGINS=*
ALGERIAN_TIMEZONE=Africa/Algiers
DEFAULT_LANGUAGE=ar
```

#### Step 5: Deploy and Initialize
1. Click "Create Web Service"
2. Wait for the build and deployment to complete
3. The database will be automatically initialized with sample data
4. Access your application at the provided Render URL

### Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@maintai.dz`

## 📱 Usage

### Dashboard Access
1. Open your Render application URL
2. Log in with the default credentials
3. Explore the different tabs:
   - **Overview**: System health and recent alerts
   - **Sensors**: Real-time sensor readings and trends
   - **Alerts**: Alert management and history
   - **Machines**: Machine status and configuration
   - **Analytics**: Predictive analytics and performance metrics

### Language Selection
- Use the language selector in the top navigation
- Supported languages: English, العربية (Arabic), Français (French)

### PLC Integration
1. Navigate to the PLC integration section
2. Configure your Siemens or Schneider PLC connection
3. Import configuration from TIA Portal or Unity Pro
4. Test the connection and start monitoring

## 🔧 Configuration

### Factory Setup
```python
# Example factory configuration
factory_config = {
    "id": "FACTORY_001",
    "name": "مصنع الجزائر الصناعي",
    "wilaya": "16",  # Alger
    "industry_type": "manufacturing",
    "plc_type": "siemens_s7",
    "plc_ip": "192.168.1.100"
}
```

### Machine Configuration
```python
# Example machine sensor configuration
sensor_config = {
    "temperature": {
        "db_number": 1,
        "address": 0,
        "data_type": "real",
        "unit": "°C"
    },
    "humidity": {
        "db_number": 1,
        "address": 4,
        "data_type": "real",
        "unit": "%"
    }
}
```

### Notification Setup
```python
# Example notification preferences
notification_config = {
    "sms": True,
    "email": True,
    "push": True,
    "language": "ar",
    "severity_filter": ["high", "critical"]
}
```

## 🏗️ Architecture

### Backend (Flask)
- **API Routes**: RESTful API for all operations
- **Database Models**: SQLAlchemy ORM with PostgreSQL
- **ML Services**: Scikit-learn based prediction models
- **PLC Integration**: Custom Siemens S7 and Schneider Modicon clients
- **Notification Services**: SMS (Twilio), Email (SMTP), IoT integration

### Frontend (Vanilla JavaScript)
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Real-time Updates**: WebSocket connections for live data
- **Charts**: Chart.js for data visualization
- **Multi-language**: Dynamic language switching

### Database Schema
- **Users**: User management and authentication
- **Factories**: Factory and location information
- **Machines**: Machine configuration and status
- **Sensor Data**: Time-series sensor readings
- **Alerts**: Alert management and history

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/user` - Get current user info

### Sensor Data
- `GET /api/sensor-data/latest` - Get latest sensor readings
- `POST /api/sensor-data` - Submit new sensor data
- `GET /api/sensor-data/{device_id}` - Get device history

### Alerts
- `GET /api/alerts` - Get alerts with filtering
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert
- `POST /api/alerts/{id}/resolve` - Resolve alert

### Machine Learning
- `POST /api/analyze` - Analyze sensor data for anomalies
- `POST /api/train-models` - Train prediction models
- `GET /api/model-status` - Get model training status

### PLC Integration
- `POST /api/plc/connect/{factory_id}` - Connect to factory PLC
- `POST /api/plc/read-sensors/{factory_id}/{machine_id}` - Read PLC sensors
- `POST /api/plc/siemens/tia-portal-export` - Import TIA Portal config

### Notifications
- `POST /api/notifications/send-alert/{alert_id}` - Send alert notification
- `POST /api/notifications/test/{user_id}` - Test notifications

## 🌍 Algerian Market Features

### Wilaya Support
All 58 Algerian provinces (wilayas) are supported with:
- Arabic and French names
- Local industrial zones
- Regional supplier networks
- Climate considerations

### Working Hours
- **Morning Shift**: 06:00 - 14:00
- **Afternoon Shift**: 14:00 - 22:00
- **Night Shift**: 22:00 - 06:00
- **Ramadan Adjustments**: Automatic working hour modifications

### Compliance
- Environmental regulations (ISO 14001)
- Safety standards (OHSAS 18001)
- Quality management (ISO 9001, IANOR)
- Maintenance reporting for authorities

### Local Integration
- Algerian phone number formatting (+213)
- DZD currency calculations
- Islamic calendar integration
- Local supplier recommendations

## 🔧 Development

### Local Development Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd maintai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/maintai_db"
export SECRET_KEY="your-secret-key"
export FLASK_ENV="development"

# Initialize database
python -m src.scripts.migrate_db

# Run the application
python -m src.main
```

### Testing
```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

### Adding New Sensors
1. Update the sensor configuration in machine settings
2. Add sensor type mapping in PLC integration
3. Update the ML models for the new sensor type
4. Add translations for the new sensor type

### Adding New Languages
1. Add translations to `src/static/js/translations.js`
2. Update language selector in the frontend
3. Add RTL support if needed (like Arabic)

## 📊 Monitoring and Maintenance

### Health Checks
- Application health: `/health`
- Database connectivity: `/health/db`
- PLC connections: `/api/plc/status`

### Logging
- Application logs: Structured JSON logging
- Error tracking: Automatic error reporting
- Performance monitoring: Request timing and metrics

### Backup
- Database: Automatic daily backups on Render
- Configuration: Version controlled in Git
- User data: Export functionality available

## 🚨 Troubleshooting

### Common Issues

**Database Connection Error**
```
Error: could not connect to server
```
Solution: Check DATABASE_URL environment variable and database status

**PLC Connection Failed**
```
Error: Failed to connect to Siemens S7 PLC
```
Solution: Verify PLC IP address, network connectivity, and firewall settings

**SMS Notifications Not Working**
```
Error: Failed to send SMS notification
```
Solution: Check Twilio credentials and phone number format

**Arabic Text Not Displaying**
```
Issue: Arabic text appears as squares
```
Solution: Ensure Arabic fonts are loaded and RTL CSS is applied

### Performance Optimization
- Enable database connection pooling
- Use Redis for caching frequent queries
- Optimize sensor data queries with proper indexing
- Implement data archiving for old sensor readings

## 📞 Support

### Documentation
- API Documentation: `/api/docs` (when running)
- User Manual: Available in Arabic and French
- Video Tutorials: Coming soon

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Community support and questions

### Commercial Support
For enterprise support, custom integrations, or consulting services, contact the development team.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Siemens and Schneider Electric for PLC documentation
- Algerian Ministry of Industry for regulatory guidance
- Open source community for the excellent libraries used
- Beta testers from Algerian industrial companies

---

**Made with ❤️ for Algerian Industry**

*صُنع بحب للصناعة الجزائرية*

*Fait avec amour pour l'industrie algérienne*

