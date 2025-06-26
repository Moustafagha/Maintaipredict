// API Client for MaintAI Dashboard
class APIClient {
    constructor() {
        this.baseURL = window.location.origin + '/api';
        this.timeout = 10000; // 10 seconds
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Dashboard Summary
    async getDashboardSummary(factoryId = null, hours = 24) {
        const params = new URLSearchParams();
        if (factoryId) params.append('factory_id', factoryId);
        params.append('hours', hours);
        
        const response = await this.request(`/dashboard/summary?${params}`);
        return response.summary || {};
    }

    // Sensor Data
    async getLatestSensorData(deviceId = null, sensorType = null, limit = 50) {
        const params = new URLSearchParams();
        if (deviceId) params.append('device_id', deviceId);
        if (sensorType) params.append('sensor_type', sensorType);
        params.append('limit', limit);
        
        const response = await this.request(`/sensor-data/latest?${params}`);
        return response.data || [];
    }

    async getSensorData(deviceId, sensorType = null, hours = 24, limit = 1000) {
        const params = new URLSearchParams();
        if (sensorType) params.append('sensor_type', sensorType);
        params.append('hours', hours);
        params.append('limit', limit);
        
        const response = await this.request(`/sensor-data/${deviceId}?${params}`);
        return response.data || [];
    }

    async sendSensorData(sensorData) {
        return await this.request('/sensor-data', {
            method: 'POST',
            body: JSON.stringify(sensorData)
        });
    }

    async sendBatchSensorData(sensorDataArray) {
        return await this.request('/sensor-data/batch', {
            method: 'POST',
            body: JSON.stringify(sensorDataArray)
        });
    }

    // Alerts
    async getAlerts(filters = {}) {
        const params = new URLSearchParams();
        
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });
        
        const response = await this.request(`/alerts?${params}`);
        return response.alerts || [];
    }

    async acknowledgeAlert(alertId, userId = 'dashboard_user') {
        return await this.request(`/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    async resolveAlert(alertId, userId = 'dashboard_user') {
        return await this.request(`/alerts/${alertId}/resolve`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    // Machines
    async getMachines(factoryId = null) {
        const params = new URLSearchParams();
        if (factoryId) params.append('factory_id', factoryId);
        
        const response = await this.request(`/machines?${params}`);
        return response.machines || [];
    }

    async getMachine(machineId) {
        const response = await this.request(`/machines/${machineId}`);
        return response.machine || {};
    }

    // Factories
    async getFactories() {
        const response = await this.request('/factories');
        return response.factories || [];
    }

    async getFactory(factoryId) {
        const response = await this.request(`/factories/${factoryId}`);
        return response.factory || {};
    }

    // Machine Learning
    async trainModels(deviceId = null, sensorType = null) {
        const body = {};
        if (deviceId) body.device_id = deviceId;
        if (sensorType) body.sensor_type = sensorType;
        
        return await this.request('/train-models', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async analyzeData(deviceId, sensorType, value, additionalData = {}) {
        const body = {
            device_id: deviceId,
            sensor_type: sensorType,
            value: value,
            ...additionalData
        };
        
        return await this.request('/analyze', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async analyzeBatchData(dataArray) {
        return await this.request('/predict-batch', {
            method: 'POST',
            body: JSON.stringify(dataArray)
        });
    }

    async getModelStatus() {
        const response = await this.request('/model-status');
        return response.models || [];
    }

    async retrainModel(deviceId, sensorType) {
        return await this.request(`/retrain/${deviceId}/${sensorType}`, {
            method: 'POST'
        });
    }

    async getThresholds() {
        const response = await this.request('/thresholds');
        return response.thresholds || {};
    }

    async updateThresholds(thresholds) {
        return await this.request('/thresholds', {
            method: 'POST',
            body: JSON.stringify(thresholds)
        });
    }

    async getPerformanceMetrics(deviceId = null, sensorType = null, days = 7) {
        const params = new URLSearchParams();
        if (deviceId) params.append('device_id', deviceId);
        if (sensorType) params.append('sensor_type', sensorType);
        params.append('days', days);
        
        const response = await this.request(`/performance-metrics?${params}`);
        return response.metrics || {};
    }

    // Notifications
    async sendAlertNotification(alertId) {
        return await this.request(`/send-alert/${alertId}`, {
            method: 'POST'
        });
    }

    async sendIoTNotification(deviceId, alertData) {
        return await this.request(`/send-iot/${deviceId}`, {
            method: 'POST',
            body: JSON.stringify(alertData)
        });
    }

    async sendMaintenanceReminder(machineId, maintenanceType, scheduledDate) {
        return await this.request('/maintenance-reminder', {
            method: 'POST',
            body: JSON.stringify({
                machine_id: machineId,
                maintenance_type: maintenanceType,
                scheduled_date: scheduledDate
            })
        });
    }

    async testNotifications(userId) {
        return await this.request(`/test/${userId}`, {
            method: 'POST'
        });
    }

    async getNotificationPreferences(userId) {
        const response = await this.request(`/preferences/${userId}`);
        return response.preferences || {};
    }

    async updateNotificationPreferences(userId, preferences) {
        return await this.request(`/preferences/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(preferences)
        });
    }

    async getNotificationChannelsStatus() {
        const response = await this.request('/channels/status');
        return response.channels || {};
    }

    async getNotificationHistory(userId = null, hours = 24, limit = 50) {
        const params = new URLSearchParams();
        if (userId) params.append('user_id', userId);
        params.append('hours', hours);
        params.append('limit', limit);
        
        const response = await this.request(`/history?${params}`);
        return response.history || [];
    }

    async sendBulkNotifications(message, severity, userIds, notificationTypes = ['sms', 'email', 'push']) {
        return await this.request('/bulk-send', {
            method: 'POST',
            body: JSON.stringify({
                message,
                severity,
                user_ids: userIds,
                notification_types: notificationTypes
            })
        });
    }

    async sendEmergencyBroadcast(message, factoryId) {
        return await this.request('/emergency-broadcast', {
            method: 'POST',
            body: JSON.stringify({
                message,
                factory_id: factoryId
            })
        });
    }

    // Users
    async getUsers(factoryId = null) {
        const params = new URLSearchParams();
        if (factoryId) params.append('factory_id', factoryId);
        
        const response = await this.request(`/users?${params}`);
        return response.users || [];
    }

    async getUser(userId) {
        const response = await this.request(`/users/${userId}`);
        return response.user || {};
    }

    async createUser(userData) {
        return await this.request('/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async updateUser(userId, userData) {
        return await this.request(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    }

    async deleteUser(userId) {
        return await this.request(`/users/${userId}`, {
            method: 'DELETE'
        });
    }

    // System Health (mock endpoint for demonstration)
    async getSystemHealth() {
        // This would be a real endpoint in production
        // For now, return mock data
        return {
            overall_status: 'healthy',
            devices: {
                total: 25,
                active: 23,
                inactive: 2
            },
            alarms: {
                total: 12,
                critical: 2,
                high: 3,
                medium: 4,
                low: 3
            },
            sensor_readings: {
                last_24h: 15420,
                last_hour: 642
            },
            system_uptime: 99.8,
            last_updated: new Date().toISOString()
        };
    }

    // Analytics (mock endpoint for demonstration)
    async getAnalytics(factoryId = null, days = 7) {
        // This would be a real endpoint in production
        // For now, return mock data
        return {
            failure_predictions: [
                { machine_id: 'MACHINE_001', predicted_hours: 168, confidence: 0.85 },
                { machine_id: 'MACHINE_002', predicted_hours: 72, confidence: 0.92 },
                { machine_id: 'MACHINE_003', predicted_hours: 240, confidence: 0.78 },
                { machine_id: 'MACHINE_004', predicted_hours: 48, confidence: 0.95 },
                { machine_id: 'MACHINE_005', predicted_hours: 120, confidence: 0.88 }
            ],
            anomaly_detection: {
                accuracy: 92.5,
                false_positive_rate: 5.2,
                total_anomalies_detected: 45
            },
            maintenance_efficiency: {
                preventive_maintenance_ratio: 78.5,
                average_downtime_hours: 2.3,
                cost_savings_percentage: 23.7
            },
            sensor_health: {
                total_sensors: 125,
                healthy: 118,
                warning: 5,
                critical: 2
            }
        };
    }

    // Utility method to check API connectivity
    async checkConnectivity() {
        try {
            await this.request('/health', { timeout: 5000 });
            return true;
        } catch (error) {
            return false;
        }
    }

    // Method to handle API errors gracefully
    handleError(error, context = '') {
        console.error(`API Error ${context}:`, error);
        
        if (error.name === 'AbortError') {
            return { error: 'Request timeout', type: 'timeout' };
        }
        
        if (error.message.includes('Failed to fetch')) {
            return { error: 'Network error', type: 'network' };
        }
        
        if (error.message.includes('HTTP error')) {
            const status = error.message.match(/status: (\d+)/)?.[1];
            return { error: `Server error (${status})`, type: 'server', status };
        }
        
        return { error: error.message || 'Unknown error', type: 'unknown' };
    }
}

// Create global API client instance
window.apiClient = new APIClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}

