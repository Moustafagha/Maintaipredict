# MaintAI Deployment Guide for Render

## دليل النشر على منصة Render

This comprehensive guide will walk you through deploying MaintAI on Render platform step by step.

## 📋 Prerequisites

Before starting the deployment, ensure you have:

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Account**: Your code repository on GitHub
3. **Basic Knowledge**: Understanding of web applications and databases
4. **Optional Services**:
   - Twilio account for SMS notifications
   - Email account for email notifications

## 🎯 Deployment Strategy

MaintAI follows a microservices architecture on Render:
- **Web Service**: Main Flask application
- **PostgreSQL Database**: Data storage
- **Redis** (Optional): Caching and session storage

## 📝 Step-by-Step Deployment

### Step 1: Prepare Your Repository

#### 1.1 Fork or Upload Code
```bash
# Option A: Fork the repository on GitHub
# Go to the repository page and click "Fork"

# Option B: Upload your code to a new repository
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/maintai.git
git push -u origin main
```

#### 1.2 Verify Required Files
Ensure these files are in your repository root:
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `Procfile` - Process definitions
- `runtime.txt` - Python version
- `src/` - Application source code

### Step 2: Create PostgreSQL Database

#### 2.1 Navigate to Render Dashboard
1. Log in to [render.com](https://render.com)
2. Click "New +" button
3. Select "PostgreSQL"

#### 2.2 Configure Database
```yaml
Name: maintai-postgres
Database Name: maintai_db
User: maintai_user
Region: Choose closest to your users (Europe for Algeria)
Plan: Starter (for testing) or Professional (for production)
```

#### 2.3 Database Settings
- **Version**: PostgreSQL 14 or later
- **Storage**: Start with 1GB, scale as needed
- **Backup**: Enable automatic backups

#### 2.4 Save Database Information
After creation, copy these values:
- **Internal Database URL**: Used by your application
- **External Database URL**: For external connections
- **Connection Parameters**: Host, Port, Database, User, Password

### Step 3: Create Web Service

#### 3.1 Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select the repository containing MaintAI code

#### 3.2 Configure Build Settings
```yaml
Name: maintai-backend
Environment: Python 3
Branch: main
Root Directory: . (leave empty if code is in root)
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT src.main:app
```

#### 3.3 Advanced Settings
```yaml
Auto-Deploy: Yes
Health Check Path: /health
```

### Step 4: Configure Environment Variables

#### 4.1 Required Variables
Add these environment variables in the Render dashboard:

```bash
# Database Configuration
DATABASE_URL=<your-postgres-internal-url>

# Application Configuration
SECRET_KEY=<generate-random-32-character-string>
FLASK_ENV=production
FLASK_APP=src.main:app

# CORS Configuration
CORS_ORIGINS=*
```

#### 4.2 Optional Variables (for full functionality)
```bash
# SMS Notifications (Twilio)
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_PHONE_NUMBER=<your-twilio-phone-number>

# Email Notifications
EMAIL_USERNAME=<your-email@gmail.com>
EMAIL_PASSWORD=<your-app-password>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Algerian Localization
ALGERIAN_TIMEZONE=Africa/Algiers
DEFAULT_LANGUAGE=ar

# Logging and Monitoring
LOG_LEVEL=INFO
ENABLE_DEBUG=false
```

#### 4.3 Generating SECRET_KEY
```python
# Run this in Python to generate a secret key
import secrets
print(secrets.token_hex(32))
```

### Step 5: Deploy Application

#### 5.1 Start Deployment
1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Build the application
   - Start the service

#### 5.2 Monitor Deployment
Watch the build logs for:
- ✅ Dependencies installation
- ✅ Database connection
- ✅ Application startup
- ✅ Health check passing

#### 5.3 Deployment Timeline
- **Build Time**: 3-5 minutes
- **Database Migration**: 1-2 minutes
- **Health Check**: 30 seconds
- **Total**: ~5-7 minutes

### Step 6: Verify Deployment

#### 6.1 Access Application
1. Open the provided Render URL
2. You should see the MaintAI login page
3. Default credentials:
   - Username: `admin`
   - Password: `admin123`

#### 6.2 Test Core Features
- [ ] Login functionality
- [ ] Dashboard loads
- [ ] Language switching works
- [ ] Database connectivity
- [ ] API endpoints respond

#### 6.3 Check Health Endpoints
```bash
# Application health
curl https://your-app.onrender.com/health

# Database health
curl https://your-app.onrender.com/health/db

# API status
curl https://your-app.onrender.com/api/dashboard/summary
```

## 🔧 Configuration

### Database Configuration

#### Connection Pooling
```python
# In your application configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}
```

#### Database Optimization
```sql
-- Run these queries to optimize performance
CREATE INDEX idx_sensor_data_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_sensor_data_device_id ON sensor_data(device_id);
CREATE INDEX idx_alerts_factory_id ON alerts(factory_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

### Application Configuration

#### Logging Configuration
```python
# Configure structured logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['default']
    }
}
```

### Security Configuration

#### CORS Settings
```python
# Configure CORS for production
CORS_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://your-app.onrender.com"
]
```

#### Rate Limiting
```python
# Add rate limiting for API endpoints
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## 📊 Monitoring and Maintenance

### Application Monitoring

#### Health Checks
Render automatically monitors:
- HTTP response codes
- Response time
- Memory usage
- CPU usage

#### Custom Metrics
```python
# Add custom health checks
@app.route('/health/detailed')
def detailed_health():
    return {
        'status': 'healthy',
        'database': check_database_connection(),
        'plc_connections': check_plc_connections(),
        'notification_services': check_notification_services(),
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Database Monitoring

#### Connection Monitoring
```sql
-- Monitor active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Monitor database size
SELECT pg_size_pretty(pg_database_size('maintai_db')) as database_size;
```

#### Performance Monitoring
```sql
-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Log Management

#### Accessing Logs
```bash
# View application logs in Render dashboard
# Or use Render CLI
render logs --service maintai-backend --tail
```

#### Log Analysis
Monitor for:
- Error patterns
- Performance bottlenecks
- Security issues
- PLC connection problems

## 🚨 Troubleshooting

### Common Deployment Issues

#### Build Failures
```bash
# Issue: Dependencies not installing
# Solution: Check requirements.txt format
pip freeze > requirements.txt

# Issue: Python version mismatch
# Solution: Update runtime.txt
echo "python-3.11.0" > runtime.txt
```

#### Database Connection Issues
```bash
# Issue: Database connection refused
# Solution: Check DATABASE_URL format
# Correct format: postgresql://user:password@host:port/database

# Issue: SSL connection error
# Solution: Add SSL parameters
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
```

#### Application Startup Issues
```bash
# Issue: Gunicorn not starting
# Solution: Check Procfile format
web: gunicorn --bind 0.0.0.0:$PORT src.main:app

# Issue: Module not found
# Solution: Check Python path and imports
export PYTHONPATH="${PYTHONPATH}:/app"
```

### Performance Issues

#### Slow Response Times
1. **Database Optimization**:
   - Add missing indexes
   - Optimize queries
   - Enable connection pooling

2. **Application Optimization**:
   - Enable caching
   - Optimize API endpoints
   - Reduce payload sizes

3. **Infrastructure Scaling**:
   - Upgrade Render plan
   - Add Redis caching
   - Optimize database plan

#### Memory Issues
```python
# Monitor memory usage
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB
```

### Security Issues

#### SSL/TLS Configuration
Render automatically provides SSL certificates, but ensure:
- All API calls use HTTPS
- Secure headers are set
- CORS is properly configured

#### Environment Variables Security
- Never commit secrets to Git
- Use Render's environment variable encryption
- Rotate secrets regularly

## 📈 Scaling and Optimization

### Horizontal Scaling

#### Multiple Web Services
```yaml
# render.yaml for multiple instances
services:
  - type: web
    name: maintai-backend-1
    # ... configuration
  - type: web
    name: maintai-backend-2
    # ... configuration
```

#### Load Balancing
Render automatically load balances between instances.

### Vertical Scaling

#### Upgrading Plans
1. **Starter**: Development and testing
2. **Standard**: Small production deployments
3. **Pro**: High-traffic applications
4. **Enterprise**: Custom requirements

### Database Scaling

#### Read Replicas
```python
# Configure read replicas for better performance
SQLALCHEMY_BINDS = {
    'read_replica': 'postgresql://...'
}
```

#### Connection Pooling
```python
# Optimize database connections
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_recycle': 300,
    'pool_pre_ping': True
}
```

## 🔄 Continuous Deployment

### Automatic Deployments

#### GitHub Integration
Render automatically deploys when you push to your main branch:
1. Push code to GitHub
2. Render detects changes
3. Automatic build and deployment
4. Health checks verify deployment

#### Deployment Hooks
```bash
# Add deployment hooks in render.yaml
services:
  - type: web
    name: maintai-backend
    buildCommand: |
      pip install -r requirements.txt
      python -m src.scripts.migrate_db
    startCommand: gunicorn --bind 0.0.0.0:$PORT src.main:app
```

### Environment Management

#### Staging Environment
```yaml
# Create staging environment
services:
  - type: web
    name: maintai-staging
    env: staging
    envVars:
      - key: FLASK_ENV
        value: staging
      - key: DATABASE_URL
        fromDatabase:
          name: maintai-postgres-staging
          property: connectionString
```

#### Production Environment
```yaml
# Production configuration
services:
  - type: web
    name: maintai-production
    env: production
    envVars:
      - key: FLASK_ENV
        value: production
      - key: LOG_LEVEL
        value: WARNING
```

## 📞 Support and Resources

### Render Documentation
- [Render Docs](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Environment Variables](https://render.com/docs/environment-variables)

### MaintAI Resources
- GitHub Repository: Your repository URL
- API Documentation: `/api/docs` endpoint
- User Manual: Available in multiple languages

### Getting Help
1. **Render Support**: Available through dashboard
2. **Community Forums**: Render community discussions
3. **GitHub Issues**: For application-specific problems

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Code is committed to GitHub
- [ ] Environment variables are documented
- [ ] Database schema is finalized
- [ ] Tests are passing
- [ ] Security review completed

### During Deployment
- [ ] Database created successfully
- [ ] Environment variables configured
- [ ] Web service deployed
- [ ] Health checks passing
- [ ] SSL certificate active

### Post-Deployment
- [ ] Application accessible via URL
- [ ] Login functionality works
- [ ] Database connectivity verified
- [ ] API endpoints responding
- [ ] Monitoring configured
- [ ] Backup strategy implemented

### Production Readiness
- [ ] Performance testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Support procedures established

---

**Congratulations! 🎉**

Your MaintAI application is now successfully deployed on Render and ready to serve the Algerian industrial market with predictive maintenance capabilities.

**تهانينا! تم نشر تطبيق MaintAI بنجاح على منصة Render**

**Félicitations! Votre application MaintAI est maintenant déployée avec succès sur Render**

