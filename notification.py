from flask import Blueprint, jsonify, request
from src.services.notification_service import notification_service
from src.models.user import User
from src.models.sensor import Alert, db
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/send-alert/<int:alert_id>', methods=['POST'])
def send_alert_notification(alert_id):
    """Send notifications for a specific alert"""
    try:
        success, message = notification_service.send_alert_notifications(alert_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'alert_id': alert_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message,
                'alert_id': alert_id
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/send-iot/<device_id>', methods=['POST'])
def send_iot_notification(device_id):
    """Send notification to IoT device"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['alert_type', 'severity', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        success, message = notification_service.send_iot_device_notification(device_id, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'device_id': device_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message,
                'device_id': device_id
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/maintenance-reminder', methods=['POST'])
def send_maintenance_reminder():
    """Send maintenance reminder notifications"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['machine_id', 'maintenance_type', 'scheduled_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        success, message = notification_service.send_maintenance_reminder(
            data['machine_id'],
            data['maintenance_type'],
            data['scheduled_date']
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/test/<int:user_id>', methods=['POST'])
def test_user_notifications(user_id):
    """Test all notification channels for a user"""
    try:
        success, result = notification_service.test_notification_channels(user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Test notifications sent',
                'results': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/preferences/<int:user_id>', methods=['GET', 'PUT'])
def manage_notification_preferences(user_id):
    """Get or update user notification preferences"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'user_id': user_id,
                'preferences': {
                    'sms_notifications': user.sms_notifications,
                    'email_notifications': user.email_notifications,
                    'push_notifications': user.push_notifications,
                    'notification_severity_threshold': user.notification_severity_threshold,
                    'phone': user.phone,
                    'email': user.email,
                    'language': user.language
                }
            })
        
        elif request.method == 'PUT':
            data = request.json
            
            # Update preferences
            if 'sms_notifications' in data:
                user.sms_notifications = bool(data['sms_notifications'])
            
            if 'email_notifications' in data:
                user.email_notifications = bool(data['email_notifications'])
            
            if 'push_notifications' in data:
                user.push_notifications = bool(data['push_notifications'])
            
            if 'notification_severity_threshold' in data:
                threshold = data['notification_severity_threshold']
                if threshold in ['low', 'medium', 'high', 'critical']:
                    user.notification_severity_threshold = threshold
            
            if 'phone' in data:
                user.phone = data['phone']
            
            if 'language' in data:
                language = data['language']
                if language in ['en', 'ar', 'fr']:
                    user.language = language
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Notification preferences updated',
                'user_id': user_id,
                'preferences': {
                    'sms_notifications': user.sms_notifications,
                    'email_notifications': user.email_notifications,
                    'push_notifications': user.push_notifications,
                    'notification_severity_threshold': user.notification_severity_threshold,
                    'phone': user.phone,
                    'email': user.email,
                    'language': user.language
                }
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/channels/status', methods=['GET'])
def get_notification_channels_status():
    """Get status of notification channels (SMS, Email, Push)"""
    try:
        # Check if notification services are configured
        status = {
            'sms': {
                'configured': bool(notification_service.twilio_client),
                'provider': 'Twilio',
                'status': 'active' if notification_service.twilio_client else 'not_configured'
            },
            'email': {
                'configured': bool(notification_service.email_username and notification_service.email_password),
                'provider': 'SMTP',
                'server': notification_service.smtp_server,
                'status': 'active' if (notification_service.email_username and notification_service.email_password) else 'not_configured'
            },
            'push': {
                'configured': True,  # Always available (simulated)
                'provider': 'Custom',
                'status': 'active'
            },
            'iot': {
                'configured': True,  # Always available (simulated)
                'provider': 'MQTT/HTTP',
                'status': 'active'
            }
        }
        
        return jsonify({
            'status': 'success',
            'channels': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/history', methods=['GET'])
def get_notification_history():
    """Get notification history (placeholder - would require notification log table)"""
    try:
        # In a real implementation, you would have a notification_logs table
        # For now, return mock data
        
        user_id = request.args.get('user_id')
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 50))
        
        # Mock notification history
        history = [
            {
                'id': 1,
                'user_id': user_id or 1,
                'alert_id': 123,
                'notification_type': 'sms',
                'status': 'sent',
                'message': 'Critical alert: High temperature detected',
                'timestamp': '2025-06-26T10:30:00Z',
                'delivery_status': 'delivered'
            },
            {
                'id': 2,
                'user_id': user_id or 1,
                'alert_id': 124,
                'notification_type': 'email',
                'status': 'sent',
                'message': 'Maintenance reminder for Machine-001',
                'timestamp': '2025-06-26T09:15:00Z',
                'delivery_status': 'delivered'
            },
            {
                'id': 3,
                'user_id': user_id or 1,
                'alert_id': 125,
                'notification_type': 'push',
                'status': 'sent',
                'message': 'Vibration anomaly detected',
                'timestamp': '2025-06-26T08:45:00Z',
                'delivery_status': 'delivered'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history),
            'filters': {
                'user_id': user_id,
                'hours': hours,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/bulk-send', methods=['POST'])
def send_bulk_notifications():
    """Send bulk notifications to multiple users"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['message', 'severity', 'user_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        message = data['message']
        severity = data['severity']
        user_ids = data['user_ids']
        notification_types = data.get('notification_types', ['sms', 'email', 'push'])
        
        if not isinstance(user_ids, list):
            return jsonify({'error': 'user_ids must be a list'}), 400
        
        results = []
        
        for user_id in user_ids:
            user = User.query.get(user_id)
            if not user:
                results.append({
                    'user_id': user_id,
                    'status': 'error',
                    'message': 'User not found'
                })
                continue
            
            user_result = {
                'user_id': user_id,
                'username': user.username,
                'status': 'success',
                'notifications': {}
            }
            
            # Send SMS if requested and user has phone
            if 'sms' in notification_types and user.phone:
                sms_success, sms_message = notification_service._send_sms(user.phone, message)
                user_result['notifications']['sms'] = {
                    'sent': sms_success,
                    'message': sms_message
                }
            
            # Send Email if requested and user has email
            if 'email' in notification_types and user.email:
                subject = f"MaintAI {severity.title()} Notification"
                email_success, email_message = notification_service._send_email(user.email, subject, message)
                user_result['notifications']['email'] = {
                    'sent': email_success,
                    'message': email_message
                }
            
            # Send Push if requested
            if 'push' in notification_types:
                push_title = f"{severity.title()} Alert"
                push_success, push_message = notification_service._send_push_notification(user_id, push_title, message)
                user_result['notifications']['push'] = {
                    'sent': push_success,
                    'message': push_message
                }
            
            results.append(user_result)
        
        return jsonify({
            'status': 'success',
            'message': f'Bulk notifications sent to {len(user_ids)} users',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/emergency-broadcast', methods=['POST'])
def emergency_broadcast():
    """Send emergency broadcast to all active users in a factory"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['message', 'factory_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        message = data['message']
        factory_id = data['factory_id']
        
        # Get all active users in the factory
        users = User.query.filter(
            User.factory_id == factory_id,
            User.is_active == True
        ).all()
        
        if not users:
            return jsonify({
                'status': 'error',
                'message': 'No active users found in factory'
            }), 404
        
        results = []
        
        for user in users:
            user_result = {
                'user_id': user.id,
                'username': user.username,
                'notifications': {}
            }
            
            # Emergency messages are sent via all channels
            emergency_message = f"EMERGENCY: {message}" if user.language != 'ar' else f"طوارئ: {message}"
            
            # Send SMS
            if user.phone:
                sms_success, sms_message = notification_service._send_sms(user.phone, emergency_message)
                user_result['notifications']['sms'] = {
                    'sent': sms_success,
                    'message': sms_message
                }
            
            # Send Email
            if user.email:
                subject = "EMERGENCY ALERT - MaintAI" if user.language != 'ar' else "تنبيه طوارئ - MaintAI"
                email_success, email_message = notification_service._send_email(user.email, subject, emergency_message)
                user_result['notifications']['email'] = {
                    'sent': email_success,
                    'message': email_message
                }
            
            # Send Push
            push_title = "EMERGENCY ALERT" if user.language != 'ar' else "تنبيه طوارئ"
            push_success, push_message = notification_service._send_push_notification(user.id, push_title, emergency_message)
            user_result['notifications']['push'] = {
                'sent': push_success,
                'message': push_message
            }
            
            results.append(user_result)
        
        return jsonify({
            'status': 'success',
            'message': f'Emergency broadcast sent to {len(users)} users',
            'factory_id': factory_id,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

