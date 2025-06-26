import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
import os
from datetime import datetime, timedelta
import json
from src.models.sensor import SensorData, Alert, db
from src.models.user import User

class MLService:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.scalers = {}
        self.anomaly_models = {}
        self.prediction_models = {}
        
    def get_sensor_data(self, device_id, sensor_type, hours=24):
        """Get recent sensor data for analysis"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        data = SensorData.query.filter(
            SensorData.device_id == device_id,
            SensorData.sensor_type == sensor_type,
            SensorData.timestamp >= cutoff_time
        ).order_by(SensorData.timestamp.asc()).all()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'value': d.value,
            'device_id': d.device_id,
            'sensor_type': d.sensor_type,
            'factory_id': d.factory_id,
            'machine_id': d.machine_id
        } for d in data])
        
        return df
    
    def prepare_features(self, df):
        """Prepare features for ML models"""
        if df.empty:
            return np.array([])
            
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Create time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Create rolling statistics
        df['rolling_mean_1h'] = df['value'].rolling(window=12, min_periods=1).mean()  # 12 * 5min = 1h
        df['rolling_std_1h'] = df['value'].rolling(window=12, min_periods=1).std()
        df['rolling_mean_4h'] = df['value'].rolling(window=48, min_periods=1).mean()  # 48 * 5min = 4h
        df['rolling_std_4h'] = df['value'].rolling(window=48, min_periods=1).std()
        
        # Create lag features
        df['lag_1'] = df['value'].shift(1)
        df['lag_5'] = df['value'].shift(5)
        df['lag_12'] = df['value'].shift(12)
        
        # Create rate of change features
        df['rate_change_1'] = df['value'].diff()
        df['rate_change_5'] = df['value'].diff(5)
        
        # Fill NaN values
        df = df.fillna(method='bfill').fillna(method='ffill')
        
        # Select features for modeling
        feature_columns = [
            'value', 'hour', 'day_of_week', 'is_weekend',
            'rolling_mean_1h', 'rolling_std_1h', 'rolling_mean_4h', 'rolling_std_4h',
            'lag_1', 'lag_5', 'lag_12', 'rate_change_1', 'rate_change_5'
        ]
        
        return df[feature_columns].values
    
    def train_anomaly_detection(self, device_id, sensor_type):
        """Train anomaly detection model for a specific device/sensor combination"""
        try:
            # Get historical data (last 30 days)
            df = self.get_sensor_data(device_id, sensor_type, hours=24*30)
            
            if df.empty or len(df) < 100:
                return False, "Insufficient data for training"
            
            # Prepare features
            features = self.prepare_features(df)
            
            if features.size == 0:
                return False, "Failed to prepare features"
            
            # Scale features
            scaler_key = f"{device_id}_{sensor_type}"
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Train Isolation Forest for anomaly detection
            model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            model.fit(features_scaled)
            
            # Save model and scaler
            model_path = os.path.join(self.models_dir, f"anomaly_{device_id}_{sensor_type}.joblib")
            scaler_path = os.path.join(self.models_dir, f"scaler_{device_id}_{sensor_type}.joblib")
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Store in memory for quick access
            self.anomaly_models[scaler_key] = model
            self.scalers[scaler_key] = scaler
            
            return True, "Anomaly detection model trained successfully"
            
        except Exception as e:
            return False, f"Error training anomaly detection model: {str(e)}"
    
    def train_failure_prediction(self, device_id, sensor_type):
        """Train failure prediction model"""
        try:
            # Get historical data with maintenance records
            df = self.get_sensor_data(device_id, sensor_type, hours=24*60)  # 60 days
            
            if df.empty or len(df) < 200:
                return False, "Insufficient data for training"
            
            # Prepare features
            features = self.prepare_features(df)
            
            if features.size == 0:
                return False, "Failed to prepare features"
            
            # Create target variable (time to next maintenance/failure)
            # This is a simplified approach - in real implementation, you'd use actual maintenance records
            target = self._create_failure_targets(df)
            
            if len(target) != len(features):
                return False, "Feature-target mismatch"
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler_key = f"{device_id}_{sensor_type}_pred"
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest for failure prediction
            model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            # Save model and scaler
            model_path = os.path.join(self.models_dir, f"prediction_{device_id}_{sensor_type}.joblib")
            scaler_path = os.path.join(self.models_dir, f"scaler_pred_{device_id}_{sensor_type}.joblib")
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Store in memory
            self.prediction_models[scaler_key] = model
            self.scalers[scaler_key] = scaler
            
            return True, f"Failure prediction model trained successfully (MSE: {mse:.4f})"
            
        except Exception as e:
            return False, f"Error training failure prediction model: {str(e)}"
    
    def _create_failure_targets(self, df):
        """Create synthetic failure targets for demonstration"""
        # In a real implementation, this would use actual maintenance/failure records
        # For now, we'll create synthetic targets based on sensor value patterns
        
        targets = []
        for i in range(len(df)):
            # Simulate time to failure based on sensor value trends
            # Higher values = shorter time to failure
            value = df.iloc[i]['value']
            
            # Normalize and create synthetic target (hours to failure)
            if value > df['value'].quantile(0.9):
                target = np.random.normal(24, 6)  # 24 hours ± 6
            elif value > df['value'].quantile(0.7):
                target = np.random.normal(72, 12)  # 72 hours ± 12
            else:
                target = np.random.normal(168, 24)  # 168 hours ± 24
            
            targets.append(max(1, target))  # Ensure positive values
        
        return np.array(targets)
    
    def detect_anomaly(self, device_id, sensor_type, current_data):
        """Detect anomalies in current sensor data"""
        try:
            scaler_key = f"{device_id}_{sensor_type}"
            
            # Load model if not in memory
            if scaler_key not in self.anomaly_models:
                model_path = os.path.join(self.models_dir, f"anomaly_{device_id}_{sensor_type}.joblib")
                scaler_path = os.path.join(self.models_dir, f"scaler_{device_id}_{sensor_type}.joblib")
                
                if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                    return False, 0.0, "Model not found. Please train the model first."
                
                self.anomaly_models[scaler_key] = joblib.load(model_path)
                self.scalers[scaler_key] = joblib.load(scaler_path)
            
            # Get recent data for context
            df = self.get_sensor_data(device_id, sensor_type, hours=4)
            
            if df.empty:
                return False, 0.0, "No historical data available"
            
            # Add current data point
            current_df = pd.DataFrame([{
                'timestamp': datetime.utcnow(),
                'value': current_data['value'],
                'device_id': device_id,
                'sensor_type': sensor_type,
                'factory_id': current_data.get('factory_id', ''),
                'machine_id': current_data.get('machine_id', '')
            }])
            
            df = pd.concat([df, current_df], ignore_index=True)
            
            # Prepare features
            features = self.prepare_features(df)
            
            if features.size == 0:
                return False, 0.0, "Failed to prepare features"
            
            # Get the last row (current data)
            current_features = features[-1:].reshape(1, -1)
            
            # Scale features
            current_features_scaled = self.scalers[scaler_key].transform(current_features)
            
            # Predict anomaly
            anomaly_score = self.anomaly_models[scaler_key].decision_function(current_features_scaled)[0]
            is_anomaly = self.anomaly_models[scaler_key].predict(current_features_scaled)[0] == -1
            
            # Convert score to confidence (0-1)
            confidence = max(0, min(1, (anomaly_score + 0.5) / 1.0))
            
            return is_anomaly, confidence, "Anomaly detection completed"
            
        except Exception as e:
            return False, 0.0, f"Error in anomaly detection: {str(e)}"
    
    def predict_failure(self, device_id, sensor_type, current_data):
        """Predict time to failure for current sensor data"""
        try:
            scaler_key = f"{device_id}_{sensor_type}_pred"
            
            # Load model if not in memory
            if scaler_key not in self.prediction_models:
                model_path = os.path.join(self.models_dir, f"prediction_{device_id}_{sensor_type}.joblib")
                scaler_path = os.path.join(self.models_dir, f"scaler_pred_{device_id}_{sensor_type}.joblib")
                
                if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                    return 0, 0.0, "Prediction model not found. Please train the model first."
                
                self.prediction_models[scaler_key] = joblib.load(model_path)
                self.scalers[scaler_key] = joblib.load(scaler_path)
            
            # Get recent data for context
            df = self.get_sensor_data(device_id, sensor_type, hours=4)
            
            if df.empty:
                return 0, 0.0, "No historical data available"
            
            # Add current data point
            current_df = pd.DataFrame([{
                'timestamp': datetime.utcnow(),
                'value': current_data['value'],
                'device_id': device_id,
                'sensor_type': sensor_type,
                'factory_id': current_data.get('factory_id', ''),
                'machine_id': current_data.get('machine_id', '')
            }])
            
            df = pd.concat([df, current_df], ignore_index=True)
            
            # Prepare features
            features = self.prepare_features(df)
            
            if features.size == 0:
                return 0, 0.0, "Failed to prepare features"
            
            # Get the last row (current data)
            current_features = features[-1:].reshape(1, -1)
            
            # Scale features
            current_features_scaled = self.scalers[scaler_key].transform(current_features)
            
            # Predict time to failure
            predicted_hours = self.prediction_models[scaler_key].predict(current_features_scaled)[0]
            
            # Calculate confidence based on model uncertainty
            # This is simplified - in practice, you'd use prediction intervals
            confidence = max(0.1, min(0.9, 1.0 / (1.0 + abs(predicted_hours - 72) / 72)))
            
            return max(1, predicted_hours), confidence, "Failure prediction completed"
            
        except Exception as e:
            return 0, 0.0, f"Error in failure prediction: {str(e)}"
    
    def create_alert(self, device_id, sensor_type, alert_type, severity, message, 
                    predicted_failure_time=None, confidence_score=None, factory_id=None, machine_id=None):
        """Create an alert in the database"""
        try:
            # Translate message to Arabic for Algerian market
            message_ar = self._translate_to_arabic(message)
            
            alert = Alert(
                device_id=device_id,
                sensor_type=sensor_type,
                alert_type=alert_type,
                severity=severity,
                message=message,
                message_ar=message_ar,
                predicted_failure_time=predicted_failure_time,
                confidence_score=confidence_score,
                factory_id=factory_id or 'unknown',
                machine_id=machine_id or 'unknown'
            )
            
            db.session.add(alert)
            db.session.commit()
            
            return alert
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _translate_to_arabic(self, message):
        """Simple translation to Arabic for common messages"""
        translations = {
            "Anomaly detected": "تم اكتشاف شذوذ",
            "High temperature detected": "تم اكتشاف درجة حرارة عالية",
            "Vibration anomaly": "شذوذ في الاهتزاز",
            "Predicted failure": "فشل متوقع",
            "Maintenance required": "الصيانة مطلوبة",
            "Critical alert": "تنبيه حرج",
            "Warning": "تحذير",
            "Normal operation": "تشغيل عادي"
        }
        
        # Simple keyword-based translation
        for en, ar in translations.items():
            if en.lower() in message.lower():
                return message.replace(en, ar)
        
        return message  # Return original if no translation found

# Global ML service instance
ml_service = MLService()

