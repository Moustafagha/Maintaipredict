import os
import json
import requests
from datetime import datetime
from twilio.rest import Client
from flask import current_app
from src.models.user import User
from src.models.sensor import Alert, db
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class NotificationService:
    def __init__(self):
        # Twilio configuration for SMS
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_username = os.environ.get('EMAIL_USERNAME')
        self.email_password = os.environ.get('EMAIL_PASSWORD')
        
        # Initialize Twilio client if credentials are available
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.twilio_client = None
    
    def send_alert_notifications(self, alert_id):
        """Send notifications for an alert to relevant users"""
        try:
            alert = Alert.query.get(alert_id)
            if not alert:
                return False, "Alert not found"
            
            # Get users who should receive notifications for this factory/machine
            users = User.query.filter(
                User.factory_id == alert.factory_id,
                User.is_active == True
            ).all()
            
            # Filter users based on severity threshold
            severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            alert_severity_level = severity_levels.get(alert.severity, 1)
            
            notification_results = []
            
            for user in users:
                user_threshold_level = severity_levels.get(user.notification_severity_threshold, 2)
                
                # Only notify if alert severity meets user's threshold
                if alert_severity_level >= user_threshold_level:
                    result = self._send_user_notifications(user, alert)
                    notification_results.append(result)
            
            return True, f"Notifications sent to {len(notification_results)} users"
            
        except Exception as e:
            return False, f"Error sending notifications: {str(e)}"
    
    def _send_user_notifications(self, user, alert):
        """Send notifications to a specific user based on their preferences"""
        results = {
            'user_id': user.id,
            'username': user.username,
            'sms': {'sent': False, 'message': ''},
            'email': {'sent': False, 'message': ''},
            'push': {'sent': False, 'message': ''}
        }
        
        # Prepare message content
        message_content = self._prepare_message_content(user, alert)
        
        # Send SMS if enabled
        if user.sms_notifications and user.phone:
            sms_success, sms_message = self._send_sms(user.phone, message_content['sms'])
            results['sms'] = {'sent': sms_success, 'message': sms_message}
        
        # Send Email if enabled
        if user.email_notifications and user.email:
            email_success, email_message = self._send_email(
                user.email, 
                message_content['email_subject'],
                message_content['email_body']
            )
            results['email'] = {'sent': email_success, 'message': email_message}
        
        # Send Push notification if enabled
        if user.push_notifications:
            push_success, push_message = self._send_push_notification(
                user.id,
                message_content['push_title'],
                message_content['push_body']
            )
            results['push'] = {'sent': push_success, 'message': push_message}
        
        return results
    
    def _prepare_message_content(self, user, alert):
        """Prepare message content in user's preferred language"""
        # Use Arabic message if available and user prefers Arabic
        if user.language == 'ar' and alert.message_ar:
            base_message = alert.message_ar
        else:
            base_message = alert.message
        
        # Prepare different message formats
        content = {
            'sms': self._prepare_sms_message(user, alert, base_message),
            'email_subject': self._prepare_email_subject(user, alert),
            'email_body': self._prepare_email_body(user, alert, base_message),
            'push_title': self._prepare_push_title(user, alert),
            'push_body': base_message
        }
        
        return content
    
    def _prepare_sms_message(self, user, alert, base_message):
        """Prepare SMS message (limited to 160 characters for standard SMS)"""
        if user.language == 'ar':
            severity_text = {
                'low': 'منخفض',
                'medium': 'متوسط', 
                'high': 'عالي',
                'critical': 'حرج'
            }.get(alert.severity, alert.severity)
            
            sms_text = f"تنبيه {severity_text}: {base_message[:100]}... - MaintAI"
        else:
            sms_text = f"ALERT {alert.severity.upper()}: {base_message[:120]}... - MaintAI"
        
        return sms_text
    
    def _prepare_email_subject(self, user, alert):
        """Prepare email subject"""
        if user.language == 'ar':
            return f"تنبيه MaintAI - {alert.severity} - {alert.machine_id}"
        else:
            return f"MaintAI Alert - {alert.severity.title()} - {alert.machine_id}"
    
    def _prepare_email_body(self, user, alert, base_message):
        """Prepare detailed email body"""
        if user.language == 'ar':
            email_body = f"""
مرحباً {user.full_name_ar or user.full_name},

تم إنشاء تنبيه جديد في نظام MaintAI:

تفاصيل التنبيه:
- النوع: {alert.alert_type}
- الخطورة: {alert.severity}
- الجهاز: {alert.device_id}
- الآلة: {alert.machine_id}
- المصنع: {alert.factory_id}
- الوقت: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

الرسالة:
{base_message}

يرجى اتخاذ الإجراء المناسب في أقرب وقت ممكن.

نظام MaintAI للصيانة التنبؤية
            """
        else:
            email_body = f"""
Hello {user.full_name},

A new alert has been generated in the MaintAI system:

Alert Details:
- Type: {alert.alert_type}
- Severity: {alert.severity}
- Device: {alert.device_id}
- Machine: {alert.machine_id}
- Factory: {alert.factory_id}
- Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{base_message}

Please take appropriate action as soon as possible.

MaintAI Predictive Maintenance System
            """
        
        return email_body
    
    def _prepare_push_title(self, user, alert):
        """Prepare push notification title"""
        if user.language == 'ar':
            return f"تنبيه {alert.severity} - {alert.machine_id}"
        else:
            return f"{alert.severity.title()} Alert - {alert.machine_id}"
    
    def _send_sms(self, phone_number, message):
        """Send SMS using Twilio"""
        try:
            if not self.twilio_client:
                return False, "Twilio not configured"
            
            # Format phone number for Algeria (+213)
            if not phone_number.startswith('+'):
                if phone_number.startswith('0'):
                    phone_number = '+213' + phone_number[1:]
                else:
                    phone_number = '+213' + phone_number
            
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            return True, f"SMS sent successfully (SID: {message.sid})"
            
        except Exception as e:
            return False, f"Failed to send SMS: {str(e)}"
    
    def _send_email(self, email_address, subject, body):
        """Send email notification"""
        try:
            if not self.email_username or not self.email_password:
                return False, "Email not configured"
            
            msg = MimeMultipart()
            msg['From'] = self.email_username
            msg['To'] = email_address
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, email_address, text)
            server.quit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def _send_push_notification(self, user_id, title, body):
        """Send push notification (placeholder for real implementation)"""
        try:
            # In a real implementation, you would integrate with:
            # - Firebase Cloud Messaging (FCM) for mobile apps
            # - Web Push API for web browsers
            # - Apple Push Notification Service (APNs) for iOS
            
            # For now, we'll simulate the push notification
            push_data = {
                'user_id': user_id,
                'title': title,
                'body': body,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'alert'
            }
            
            # In production, you would send this to your push notification service
            # For demonstration, we'll just log it
            print(f"Push notification would be sent: {json.dumps(push_data, indent=2)}")
            
            return True, "Push notification queued"
            
        except Exception as e:
            return False, f"Failed to send push notification: {str(e)}"
    
    def send_iot_device_notification(self, device_id, alert_data):
        """Send notification to IoT devices (displays, lights, etc.)"""
        try:
            # Prepare IoT notification payload
            iot_payload = {
                'device_id': device_id,
                'alert_type': alert_data.get('alert_type', 'unknown'),
                'severity': alert_data.get('severity', 'medium'),
                'message': alert_data.get('message', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'action': self._determine_iot_action(alert_data.get('severity', 'medium'))
            }
            
            # Send to IoT device via HTTP/MQTT (placeholder)
            # In real implementation, you would:
            # 1. Use MQTT broker to send to IoT devices
            # 2. Use HTTP API calls to device endpoints
            # 3. Use industrial protocols like Modbus, OPC-UA
            
            success = self._send_to_iot_device(device_id, iot_payload)
            
            if success:
                return True, "IoT device notification sent"
            else:
                return False, "Failed to send IoT device notification"
                
        except Exception as e:
            return False, f"Error sending IoT notification: {str(e)}"
    
    def _determine_iot_action(self, severity):
        """Determine IoT device action based on alert severity"""
        actions = {
            'low': {
                'display': 'show_blue_light',
                'sound': 'single_beep',
                'message_display': True
            },
            'medium': {
                'display': 'show_yellow_light',
                'sound': 'double_beep',
                'message_display': True
            },
            'high': {
                'display': 'show_orange_light',
                'sound': 'triple_beep',
                'message_display': True
            },
            'critical': {
                'display': 'show_red_light_flashing',
                'sound': 'continuous_alarm',
                'message_display': True,
                'emergency_stop': False  # Set to True if needed
            }
        }
        
        return actions.get(severity, actions['medium'])
    
    def _send_to_iot_device(self, device_id, payload):
        """Send payload to IoT device (placeholder implementation)"""
        try:
            # In a real implementation, this would:
            # 1. Connect to MQTT broker
            # 2. Publish to device-specific topic
            # 3. Handle device acknowledgments
            
            # For demonstration, we'll simulate the call
            print(f"IoT notification to device {device_id}: {json.dumps(payload, indent=2)}")
            
            # Simulate successful delivery
            return True
            
        except Exception as e:
            print(f"Error sending to IoT device {device_id}: {str(e)}")
            return False
    
    def send_maintenance_reminder(self, machine_id, maintenance_type, scheduled_date):
        """Send maintenance reminder notifications"""
        try:
            # Get users responsible for this machine
            machine_query = db.session.query(
                User.id, User.username, User.email, User.phone, User.language,
                User.full_name, User.full_name_ar
            ).filter(
                User.role.in_(['technician', 'manager']),
                User.is_active == True
            )
            
            users = machine_query.all()
            
            notification_results = []
            
            for user in users:
                # Prepare maintenance reminder message
                if user.language == 'ar':
                    message = f"تذكير صيانة: {maintenance_type} مجدولة لـ {machine_id} في {scheduled_date}"
                    subject = f"تذكير صيانة - {machine_id}"
                else:
                    message = f"Maintenance Reminder: {maintenance_type} scheduled for {machine_id} on {scheduled_date}"
                    subject = f"Maintenance Reminder - {machine_id}"
                
                # Send notifications
                result = {
                    'user_id': user.id,
                    'username': user.username,
                    'sms': {'sent': False, 'message': ''},
                    'email': {'sent': False, 'message': ''}
                }
                
                if user.phone:
                    sms_success, sms_message = self._send_sms(user.phone, message)
                    result['sms'] = {'sent': sms_success, 'message': sms_message}
                
                if user.email:
                    email_success, email_message = self._send_email(user.email, subject, message)
                    result['email'] = {'sent': email_success, 'message': email_message}
                
                notification_results.append(result)
            
            return True, f"Maintenance reminders sent to {len(notification_results)} users"
            
        except Exception as e:
            return False, f"Error sending maintenance reminders: {str(e)}"
    
    def test_notification_channels(self, user_id):
        """Test all notification channels for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            test_results = {
                'user_id': user_id,
                'username': user.username,
                'sms': {'sent': False, 'message': ''},
                'email': {'sent': False, 'message': ''},
                'push': {'sent': False, 'message': ''}
            }
            
            # Test SMS
            if user.phone:
                test_message = "Test message from MaintAI system" if user.language != 'ar' else "رسالة اختبار من نظام MaintAI"
                sms_success, sms_message = self._send_sms(user.phone, test_message)
                test_results['sms'] = {'sent': sms_success, 'message': sms_message}
            
            # Test Email
            if user.email:
                subject = "MaintAI Test Notification" if user.language != 'ar' else "إشعار اختبار MaintAI"
                body = "This is a test notification from MaintAI system." if user.language != 'ar' else "هذا إشعار اختبار من نظام MaintAI."
                email_success, email_message = self._send_email(user.email, subject, body)
                test_results['email'] = {'sent': email_success, 'message': email_message}
            
            # Test Push
            push_title = "MaintAI Test" if user.language != 'ar' else "اختبار MaintAI"
            push_body = "Test notification" if user.language != 'ar' else "إشعار اختبار"
            push_success, push_message = self._send_push_notification(user_id, push_title, push_body)
            test_results['push'] = {'sent': push_success, 'message': push_message}
            
            return True, test_results
            
        except Exception as e:
            return False, f"Error testing notifications: {str(e)}"

# Global notification service instance
notification_service = NotificationService()

