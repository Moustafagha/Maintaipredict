import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.models.sensor import Factory, Machine, Alert, SensorData, db
from src.models.user import User

class AlgerianMarketService:
    """Service for Algerian market-specific customizations"""
    
    def __init__(self):
        # Algerian wilayas (provinces)
        self.wilayas = {
            '01': 'Adrar', '02': 'Chlef', '03': 'Laghouat', '04': 'Oum El Bouaghi',
            '05': 'Batna', '06': 'Béjaïa', '07': 'Biskra', '08': 'Béchar',
            '09': 'Blida', '10': 'Bouira', '11': 'Tamanrasset', '12': 'Tébessa',
            '13': 'Tlemcen', '14': 'Tiaret', '15': 'Tizi Ouzou', '16': 'Alger',
            '17': 'Djelfa', '18': 'Jijel', '19': 'Sétif', '20': 'Saïda',
            '21': 'Skikda', '22': 'Sidi Bel Abbès', '23': 'Annaba', '24': 'Guelma',
            '25': 'Constantine', '26': 'Médéa', '27': 'Mostaganem', '28': 'M\'Sila',
            '29': 'Mascara', '30': 'Ouargla', '31': 'Oran', '32': 'El Bayadh',
            '33': 'Illizi', '34': 'Bordj Bou Arréridj', '35': 'Boumerdès',
            '36': 'El Tarf', '37': 'Tindouf', '38': 'Tissemsilt', '39': 'El Oued',
            '40': 'Khenchela', '41': 'Souk Ahras', '42': 'Tipaza', '43': 'Mila',
            '44': 'Aïn Defla', '45': 'Naâma', '46': 'Aïn Témouchent', '47': 'Ghardaïa',
            '48': 'Relizane', '49': 'Timimoun', '50': 'Bordj Badji Mokhtar',
            '51': 'Ouled Djellal', '52': 'Béni Abbès', '53': 'In Salah',
            '54': 'In Guezzam', '55': 'Touggourt', '56': 'Djanet', '57': 'El M\'Ghair',
            '58': 'El Meniaa'
        }
        
        # Common Algerian industrial sectors
        self.industrial_sectors = {
            'textile': 'النسيج',
            'automotive': 'السيارات',
            'food_processing': 'تصنيع الأغذية',
            'petrochemical': 'البتروكيماويات',
            'steel': 'الصلب',
            'cement': 'الإسمنت',
            'pharmaceuticals': 'الأدوية',
            'electronics': 'الإلكترونيات',
            'mining': 'التعدين',
            'agriculture': 'الزراعة'
        }
        
        # Algerian working hours and shifts
        self.working_hours = {
            'morning': {'start': '06:00', 'end': '14:00'},
            'afternoon': {'start': '14:00', 'end': '22:00'},
            'night': {'start': '22:00', 'end': '06:00'}
        }
        
        # Algerian holidays and special considerations
        self.holidays = [
            {'name': 'New Year', 'date': '01-01', 'name_ar': 'رأس السنة الميلادية'},
            {'name': 'Labour Day', 'date': '05-01', 'name_ar': 'عيد العمال'},
            {'name': 'Independence Day', 'date': '07-05', 'name_ar': 'عيد الاستقلال'},
            {'name': 'Revolution Day', 'date': '11-01', 'name_ar': 'عيد الثورة'},
            # Islamic holidays (dates vary each year)
            {'name': 'Eid al-Fitr', 'name_ar': 'عيد الفطر', 'islamic': True},
            {'name': 'Eid al-Adha', 'name_ar': 'عيد الأضحى', 'islamic': True},
            {'name': 'Mawlid', 'name_ar': 'المولد النبوي', 'islamic': True},
            {'name': 'Muharram', 'name_ar': 'رأس السنة الهجرية', 'islamic': True}
        ]
    
    def get_wilaya_info(self, wilaya_code: str) -> Dict[str, str]:
        """Get wilaya information"""
        return {
            'code': wilaya_code,
            'name': self.wilayas.get(wilaya_code, 'Unknown'),
            'name_ar': self._get_wilaya_arabic_name(wilaya_code)
        }
    
    def _get_wilaya_arabic_name(self, wilaya_code: str) -> str:
        """Get Arabic name for wilaya"""
        arabic_names = {
            '16': 'الجزائر', '31': 'وهران', '25': 'قسنطينة', '06': 'بجاية',
            '15': 'تيزي وزو', '19': 'سطيف', '09': 'البليدة', '05': 'باتنة',
            '21': 'سكيكدة', '23': 'عنابة', '13': 'تلمسان', '27': 'مستغانم',
            '02': 'الشلف', '14': 'تيارت', '22': 'سيدي بلعباس', '26': 'المدية'
        }
        return arabic_names.get(wilaya_code, self.wilayas.get(wilaya_code, 'Unknown'))
    
    def get_current_shift(self) -> Dict[str, str]:
        """Get current work shift based on Algerian time"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        if '06:00' <= current_time < '14:00':
            return {
                'shift': 'morning',
                'name': 'Morning Shift',
                'name_ar': 'وردية الصباح',
                'start': '06:00',
                'end': '14:00'
            }
        elif '14:00' <= current_time < '22:00':
            return {
                'shift': 'afternoon',
                'name': 'Afternoon Shift',
                'name_ar': 'وردية بعد الظهر',
                'start': '14:00',
                'end': '22:00'
            }
        else:
            return {
                'shift': 'night',
                'name': 'Night Shift',
                'name_ar': 'وردية الليل',
                'start': '22:00',
                'end': '06:00'
            }
    
    def is_working_day(self, date: datetime = None) -> Dict[str, Any]:
        """Check if it's a working day in Algeria"""
        if date is None:
            date = datetime.now()
        
        # Friday and Saturday are weekend in Algeria
        is_weekend = date.weekday() in [4, 5]  # Friday=4, Saturday=5
        
        # Check for national holidays
        date_str = date.strftime('%m-%d')
        is_holiday = any(holiday['date'] == date_str for holiday in self.holidays if 'date' in holiday)
        
        return {
            'is_working_day': not (is_weekend or is_holiday),
            'is_weekend': is_weekend,
            'is_holiday': is_holiday,
            'day_type': 'weekend' if is_weekend else ('holiday' if is_holiday else 'working_day'),
            'day_type_ar': 'عطلة نهاية الأسبوع' if is_weekend else ('عطلة رسمية' if is_holiday else 'يوم عمل')
        }
    
    def get_ramadan_adjustments(self, date: datetime = None) -> Dict[str, Any]:
        """Get Ramadan working hour adjustments"""
        if date is None:
            date = datetime.now()
        
        # This is a simplified check - in production, you'd use a proper Islamic calendar
        # For demonstration, assume Ramadan is in April (varies each year)
        is_ramadan = date.month == 4  # Simplified
        
        if is_ramadan:
            return {
                'is_ramadan': True,
                'adjusted_hours': {
                    'morning': {'start': '07:00', 'end': '13:00'},
                    'afternoon': {'start': '15:00', 'end': '19:00'}
                },
                'message': 'Working hours adjusted for Ramadan',
                'message_ar': 'تم تعديل ساعات العمل لشهر رمضان'
            }
        
        return {
            'is_ramadan': False,
            'adjusted_hours': None,
            'message': 'Normal working hours',
            'message_ar': 'ساعات العمل العادية'
        }
    
    def format_alert_for_algeria(self, alert: Alert, user_language: str = 'ar') -> Dict[str, str]:
        """Format alert message for Algerian context"""
        # Get wilaya information if available
        factory = Factory.query.get(alert.factory_id)
        wilaya_info = ""
        if factory and factory.wilaya:
            wilaya_data = self.get_wilaya_info(factory.wilaya)
            if user_language == 'ar':
                wilaya_info = f" - {wilaya_data['name_ar']}"
            else:
                wilaya_info = f" - {wilaya_data['name']}"
        
        # Get current shift information
        shift_info = self.get_current_shift()
        
        if user_language == 'ar':
            formatted_message = f"""
تنبيه من نظام MaintAI
المصنع: {alert.factory_id}{wilaya_info}
الآلة: {alert.machine_id}
نوع التنبيه: {self._translate_alert_type_ar(alert.alert_type)}
الخطورة: {self._translate_severity_ar(alert.severity)}
الوردية: {shift_info['name_ar']}
الوقت: {alert.timestamp.strftime('%Y-%m-%d %H:%M')}

الرسالة: {alert.message_ar or alert.message}

يرجى اتخاذ الإجراء المناسب فوراً.
            """.strip()
        else:
            formatted_message = f"""
MaintAI System Alert
Factory: {alert.factory_id}{wilaya_info}
Machine: {alert.machine_id}
Alert Type: {alert.alert_type}
Severity: {alert.severity}
Shift: {shift_info['name']}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M')}

Message: {alert.message}

Please take immediate action.
            """.strip()
        
        return {
            'formatted_message': formatted_message,
            'wilaya_info': wilaya_info,
            'shift_info': shift_info,
            'language': user_language
        }
    
    def _translate_alert_type_ar(self, alert_type: str) -> str:
        """Translate alert type to Arabic"""
        translations = {
            'anomaly': 'شذوذ',
            'prediction': 'توقع',
            'threshold': 'تجاوز حد',
            'maintenance': 'صيانة',
            'emergency': 'طوارئ'
        }
        return translations.get(alert_type, alert_type)
    
    def _translate_severity_ar(self, severity: str) -> str:
        """Translate severity to Arabic"""
        translations = {
            'low': 'منخفض',
            'medium': 'متوسط',
            'high': 'عالي',
            'critical': 'حرج'
        }
        return translations.get(severity, severity)
    
    def get_algerian_phone_format(self, phone: str) -> str:
        """Format phone number for Algeria (+213)"""
        # Remove any existing country code and formatting
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if clean_phone.startswith('213'):
            return f"+{clean_phone}"
        elif clean_phone.startswith('0'):
            return f"+213{clean_phone[1:]}"
        elif len(clean_phone) == 9:
            return f"+213{clean_phone}"
        else:
            return f"+213{clean_phone}"
    
    def get_factory_compliance_info(self, factory_id: str) -> Dict[str, Any]:
        """Get compliance information for Algerian regulations"""
        factory = Factory.query.get(factory_id)
        if not factory:
            return {}
        
        # Algerian industrial regulations and standards
        compliance_requirements = {
            'environmental': {
                'required': True,
                'standards': ['ISO 14001', 'Algerian Environmental Law'],
                'description': 'Environmental management compliance',
                'description_ar': 'الامتثال لإدارة البيئة'
            },
            'safety': {
                'required': True,
                'standards': ['OHSAS 18001', 'Algerian Labor Safety Code'],
                'description': 'Occupational health and safety',
                'description_ar': 'الصحة والسلامة المهنية'
            },
            'quality': {
                'required': True,
                'standards': ['ISO 9001', 'IANOR Standards'],
                'description': 'Quality management systems',
                'description_ar': 'أنظمة إدارة الجودة'
            }
        }
        
        return {
            'factory_id': factory_id,
            'wilaya': factory.wilaya,
            'industry_type': factory.industry_type,
            'compliance_requirements': compliance_requirements,
            'last_inspection': None,  # Would be from database
            'next_inspection': None,  # Would be calculated
            'compliance_status': 'compliant'  # Would be calculated
        }
    
    def generate_maintenance_report_algeria(self, factory_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate maintenance report for Algerian authorities"""
        factory = Factory.query.get(factory_id)
        if not factory:
            return {}
        
        # Get maintenance data
        machines = Machine.query.filter_by(factory_id=factory_id).all()
        alerts = Alert.query.filter(
            Alert.factory_id == factory_id,
            Alert.timestamp >= start_date,
            Alert.timestamp <= end_date
        ).all()
        
        # Calculate statistics
        total_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.severity == 'critical'])
        resolved_alerts = len([a for a in alerts if a.resolved])
        
        # Working days calculation
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if self.is_working_day(current_date)['is_working_day']:
                working_days += 1
            current_date += timedelta(days=1)
        
        report = {
            'factory_info': {
                'id': factory_id,
                'name': factory.name,
                'name_ar': factory.name_ar,
                'wilaya': factory.wilaya,
                'wilaya_name': self.get_wilaya_info(factory.wilaya)['name'],
                'industry_type': factory.industry_type,
                'manager': factory.manager_name
            },
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': (end_date - start_date).days + 1,
                'working_days': working_days
            },
            'statistics': {
                'total_machines': len(machines),
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'resolved_alerts': resolved_alerts,
                'resolution_rate': (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0,
                'alerts_per_working_day': total_alerts / working_days if working_days > 0 else 0
            },
            'compliance': self.get_factory_compliance_info(factory_id),
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'MaintAI System'
        }
        
        return report
    
    def get_local_supplier_recommendations(self, equipment_type: str, wilaya: str = None) -> List[Dict[str, str]]:
        """Get local supplier recommendations for Algeria"""
        # This would typically connect to a database of Algerian suppliers
        # For demonstration, return mock data
        
        suppliers = [
            {
                'name': 'ENIE (Entreprise Nationale des Industries Électroniques)',
                'name_ar': 'المؤسسة الوطنية للصناعات الإلكترونية',
                'location': 'Sidi Bel Abbès',
                'wilaya': '22',
                'speciality': 'Electronics, Automation',
                'contact': '+213 48 XX XX XX'
            },
            {
                'name': 'SNVI (Société Nationale des Véhicules Industriels)',
                'name_ar': 'الشركة الوطنية للمركبات الصناعية',
                'location': 'Rouiba, Alger',
                'wilaya': '16',
                'speciality': 'Industrial Vehicles, Heavy Machinery',
                'contact': '+213 21 XX XX XX'
            },
            {
                'name': 'ALFAPIPE',
                'name_ar': 'ألفابايب',
                'location': 'Oran',
                'wilaya': '31',
                'speciality': 'Pipes, Industrial Equipment',
                'contact': '+213 41 XX XX XX'
            }
        ]
        
        # Filter by wilaya if specified
        if wilaya:
            suppliers = [s for s in suppliers if s['wilaya'] == wilaya]
        
        return suppliers
    
    def calculate_energy_costs_algeria(self, consumption_kwh: float, tariff_type: str = 'industrial') -> Dict[str, float]:
        """Calculate energy costs based on Algerian tariffs"""
        # Algerian electricity tariffs (simplified - actual tariffs vary)
        tariffs = {
            'industrial': {
                'base_rate': 4.5,  # DZD per kWh
                'peak_multiplier': 1.3,
                'off_peak_multiplier': 0.8
            },
            'commercial': {
                'base_rate': 6.2,
                'peak_multiplier': 1.2,
                'off_peak_multiplier': 0.9
            }
        }
        
        tariff = tariffs.get(tariff_type, tariffs['industrial'])
        base_cost = consumption_kwh * tariff['base_rate']
        
        return {
            'consumption_kwh': consumption_kwh,
            'base_cost_dzd': base_cost,
            'peak_cost_dzd': base_cost * tariff['peak_multiplier'],
            'off_peak_cost_dzd': base_cost * tariff['off_peak_multiplier'],
            'tariff_type': tariff_type,
            'currency': 'DZD'
        }
    
    def get_weather_impact_analysis(self, wilaya: str) -> Dict[str, Any]:
        """Get weather impact analysis for industrial operations"""
        # This would typically connect to weather APIs
        # For demonstration, return mock data based on Algerian climate
        
        climate_data = {
            '16': {  # Alger
                'climate_type': 'Mediterranean',
                'avg_temp_summer': 28,
                'avg_temp_winter': 12,
                'humidity_avg': 65,
                'seasonal_considerations': {
                    'summer': 'High temperatures may affect equipment cooling',
                    'winter': 'Mild temperatures, minimal impact',
                    'spring': 'Optimal conditions for maintenance',
                    'autumn': 'Good conditions, prepare for winter'
                }
            },
            '30': {  # Ouargla
                'climate_type': 'Desert',
                'avg_temp_summer': 42,
                'avg_temp_winter': 18,
                'humidity_avg': 25,
                'seasonal_considerations': {
                    'summer': 'Extreme heat requires enhanced cooling systems',
                    'winter': 'Optimal conditions for heavy maintenance',
                    'spring': 'Good conditions before summer heat',
                    'autumn': 'Prepare equipment for temperature variations'
                }
            }
        }
        
        return climate_data.get(wilaya, {
            'climate_type': 'Unknown',
            'message': 'Climate data not available for this wilaya'
        })

# Global Algerian market service instance
algerian_service = AlgerianMarketService()

