import socket
import struct
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from src.models.sensor import SensorData, Factory, Machine, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SiemensS7Client:
    """Client for Siemens S7 PLC communication"""
    
    def __init__(self, ip_address: str, rack: int = 0, slot: int = 1):
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self.socket = None
        self.connected = False
        self.connection_id = 0
        
    def connect(self) -> bool:
        """Connect to Siemens S7 PLC"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.ip_address, 102))
            
            # Send connection request
            if self._send_connection_request():
                self.connected = True
                logger.info(f"Connected to Siemens S7 PLC at {self.ip_address}")
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Siemens S7 PLC: {str(e)}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        logger.info(f"Disconnected from Siemens S7 PLC at {self.ip_address}")
    
    def _send_connection_request(self) -> bool:
        """Send ISO connection request"""
        try:
            # ISO connection request packet
            iso_cr = bytearray([
                0x03, 0x00, 0x00, 0x16,  # TPKT Header
                0x11, 0xE0, 0x00, 0x00, 0x00, 0x01, 0x00,
                0xC0, 0x01, 0x0A,
                0xC1, 0x02, 0x01, 0x00,
                0xC2, 0x02, 0x01, 0x02
            ])
            
            self.socket.send(iso_cr)
            response = self.socket.recv(1024)
            
            # Check if connection accepted
            if len(response) >= 6 and response[5] == 0xD0:
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error sending connection request: {str(e)}")
            return False
    
    def read_db(self, db_number: int, start: int, size: int) -> Optional[bytes]:
        """Read data from DB (Data Block)"""
        if not self.connected:
            return None
            
        try:
            # S7 Read request
            read_request = self._build_read_request(db_number, start, size)
            self.socket.send(read_request)
            
            response = self.socket.recv(1024)
            return self._parse_read_response(response)
            
        except Exception as e:
            logger.error(f"Error reading DB{db_number}: {str(e)}")
            return None
    
    def write_db(self, db_number: int, start: int, data: bytes) -> bool:
        """Write data to DB (Data Block)"""
        if not self.connected:
            return False
            
        try:
            # S7 Write request
            write_request = self._build_write_request(db_number, start, data)
            self.socket.send(write_request)
            
            response = self.socket.recv(1024)
            return self._parse_write_response(response)
            
        except Exception as e:
            logger.error(f"Error writing to DB{db_number}: {str(e)}")
            return False
    
    def _build_read_request(self, db_number: int, start: int, size: int) -> bytes:
        """Build S7 read request packet"""
        # Simplified S7 read request - in production, use proper S7 protocol library
        request = bytearray([
            0x03, 0x00, 0x00, 0x1F,  # TPKT Header
            0x02, 0xF0, 0x80,        # COTP Header
            0x32, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0E,  # S7 Header
            0x00, 0x00, 0x04, 0x01,  # Parameter
            0x12, 0x0A, 0x10, 0x02,  # Item specification
            0x00, 0x01,              # Length
            0x00, db_number,         # DB number
            0x84,                    # Area (DB)
            start >> 16, start >> 8, start & 0xFF,  # Start address
            0x00, size >> 8, size & 0xFF  # Size
        ])
        return bytes(request)
    
    def _build_write_request(self, db_number: int, start: int, data: bytes) -> bytes:
        """Build S7 write request packet"""
        # Simplified S7 write request
        size = len(data)
        request = bytearray([
            0x03, 0x00, 0x00, 0x1F + size,  # TPKT Header
            0x02, 0xF0, 0x80,               # COTP Header
            0x32, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0E,  # S7 Header
            0x00, 0x00, 0x05, 0x01,         # Parameter (write)
            0x12, 0x0A, 0x10, 0x02,         # Item specification
            0x00, 0x01,                     # Length
            0x00, db_number,                # DB number
            0x84,                           # Area (DB)
            start >> 16, start >> 8, start & 0xFF,  # Start address
            0x00, size >> 8, size & 0xFF    # Size
        ])
        request.extend(data)
        return bytes(request)
    
    def _parse_read_response(self, response: bytes) -> Optional[bytes]:
        """Parse S7 read response"""
        if len(response) < 25:
            return None
        
        # Check for successful response
        if response[21] == 0xFF:  # Success
            data_length = (response[23] << 8) | response[24]
            if len(response) >= 25 + data_length:
                return response[25:25 + data_length]
        
        return None
    
    def _parse_write_response(self, response: bytes) -> bool:
        """Parse S7 write response"""
        if len(response) < 22:
            return False
        
        # Check for successful response
        return response[21] == 0xFF

class SchneiderModiconClient:
    """Client for Schneider Modicon PLC communication using Modbus TCP"""
    
    def __init__(self, ip_address: str, port: int = 502, unit_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.unit_id = unit_id
        self.socket = None
        self.connected = False
        self.transaction_id = 0
        
    def connect(self) -> bool:
        """Connect to Schneider Modicon PLC"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.ip_address, self.port))
            self.connected = True
            logger.info(f"Connected to Schneider Modicon PLC at {self.ip_address}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Schneider Modicon PLC: {str(e)}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        logger.info(f"Disconnected from Schneider Modicon PLC at {self.ip_address}")
    
    def read_holding_registers(self, address: int, count: int) -> Optional[List[int]]:
        """Read holding registers (function code 03)"""
        if not self.connected:
            return None
            
        try:
            self.transaction_id += 1
            request = self._build_modbus_request(0x03, address, count)
            self.socket.send(request)
            
            response = self.socket.recv(1024)
            return self._parse_read_registers_response(response)
            
        except Exception as e:
            logger.error(f"Error reading holding registers: {str(e)}")
            return None
    
    def write_single_register(self, address: int, value: int) -> bool:
        """Write single register (function code 06)"""
        if not self.connected:
            return False
            
        try:
            self.transaction_id += 1
            request = self._build_modbus_request(0x06, address, value)
            self.socket.send(request)
            
            response = self.socket.recv(1024)
            return self._parse_write_response(response)
            
        except Exception as e:
            logger.error(f"Error writing register: {str(e)}")
            return False
    
    def write_multiple_registers(self, address: int, values: List[int]) -> bool:
        """Write multiple registers (function code 16)"""
        if not self.connected:
            return False
            
        try:
            self.transaction_id += 1
            request = self._build_modbus_write_multiple_request(address, values)
            self.socket.send(request)
            
            response = self.socket.recv(1024)
            return self._parse_write_response(response)
            
        except Exception as e:
            logger.error(f"Error writing multiple registers: {str(e)}")
            return False
    
    def _build_modbus_request(self, function_code: int, address: int, data: int) -> bytes:
        """Build Modbus TCP request"""
        request = struct.pack('>HHHBBHH',
            self.transaction_id,  # Transaction ID
            0x0000,              # Protocol ID
            0x0006,              # Length
            self.unit_id,        # Unit ID
            function_code,       # Function code
            address,             # Starting address
            data                 # Data
        )
        return request
    
    def _build_modbus_write_multiple_request(self, address: int, values: List[int]) -> bytes:
        """Build Modbus write multiple registers request"""
        count = len(values)
        byte_count = count * 2
        
        header = struct.pack('>HHHBBHHB',
            self.transaction_id,  # Transaction ID
            0x0000,              # Protocol ID
            7 + byte_count,      # Length
            self.unit_id,        # Unit ID
            0x10,                # Function code (write multiple)
            address,             # Starting address
            count,               # Quantity of registers
            byte_count           # Byte count
        )
        
        data = b''.join(struct.pack('>H', value) for value in values)
        return header + data
    
    def _parse_read_registers_response(self, response: bytes) -> Optional[List[int]]:
        """Parse read registers response"""
        if len(response) < 9:
            return None
        
        # Check transaction ID and function code
        trans_id, proto_id, length, unit_id, func_code, byte_count = struct.unpack('>HHHBBB', response[:9])
        
        if func_code & 0x80:  # Error response
            return None
        
        # Extract register values
        values = []
        for i in range(byte_count // 2):
            value = struct.unpack('>H', response[9 + i*2:11 + i*2])[0]
            values.append(value)
        
        return values
    
    def _parse_write_response(self, response: bytes) -> bool:
        """Parse write response"""
        if len(response) < 8:
            return False
        
        func_code = response[7]
        return not (func_code & 0x80)  # Check if error bit is not set

class PLCIntegrationService:
    """Main service for PLC integration"""
    
    def __init__(self):
        self.siemens_clients = {}
        self.schneider_clients = {}
        self.active_connections = {}
        
    def connect_to_factory_plcs(self, factory_id: str) -> Dict[str, bool]:
        """Connect to all PLCs in a factory"""
        factory = Factory.query.get(factory_id)
        if not factory:
            return {}
        
        results = {}
        
        if factory.plc_type and factory.plc_ip:
            if factory.plc_type.startswith('siemens'):
                client = SiemensS7Client(factory.plc_ip)
                if client.connect():
                    self.siemens_clients[factory_id] = client
                    self.active_connections[factory_id] = {
                        'type': 'siemens',
                        'client': client,
                        'connected_at': datetime.utcnow()
                    }
                    results[factory_id] = True
                else:
                    results[factory_id] = False
                    
            elif factory.plc_type.startswith('schneider'):
                port = factory.plc_port or 502
                client = SchneiderModiconClient(factory.plc_ip, port)
                if client.connect():
                    self.schneider_clients[factory_id] = client
                    self.active_connections[factory_id] = {
                        'type': 'schneider',
                        'client': client,
                        'connected_at': datetime.utcnow()
                    }
                    results[factory_id] = True
                else:
                    results[factory_id] = False
        
        return results
    
    def disconnect_factory_plcs(self, factory_id: str):
        """Disconnect from factory PLCs"""
        if factory_id in self.siemens_clients:
            self.siemens_clients[factory_id].disconnect()
            del self.siemens_clients[factory_id]
        
        if factory_id in self.schneider_clients:
            self.schneider_clients[factory_id].disconnect()
            del self.schneider_clients[factory_id]
        
        if factory_id in self.active_connections:
            del self.active_connections[factory_id]
    
    def read_sensor_data_from_plc(self, factory_id: str, machine_id: str, sensor_config: Dict) -> Optional[Dict]:
        """Read sensor data from PLC based on configuration"""
        if factory_id not in self.active_connections:
            return None
        
        connection = self.active_connections[factory_id]
        client = connection['client']
        
        try:
            if connection['type'] == 'siemens':
                return self._read_siemens_sensor_data(client, sensor_config)
            elif connection['type'] == 'schneider':
                return self._read_schneider_sensor_data(client, sensor_config)
        except Exception as e:
            logger.error(f"Error reading sensor data from PLC: {str(e)}")
            return None
    
    def _read_siemens_sensor_data(self, client: SiemensS7Client, sensor_config: Dict) -> Optional[Dict]:
        """Read sensor data from Siemens PLC"""
        sensor_data = {}
        
        for sensor_type, config in sensor_config.items():
            if 'db_number' in config and 'address' in config:
                db_number = config['db_number']
                address = config['address']
                data_type = config.get('data_type', 'real')  # real, int, bool
                
                if data_type == 'real':
                    raw_data = client.read_db(db_number, address, 4)  # 4 bytes for REAL
                    if raw_data:
                        value = struct.unpack('>f', raw_data)[0]  # Big-endian float
                        sensor_data[sensor_type] = {
                            'value': value,
                            'unit': config.get('unit', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                elif data_type == 'int':
                    raw_data = client.read_db(db_number, address, 2)  # 2 bytes for INT
                    if raw_data:
                        value = struct.unpack('>h', raw_data)[0]  # Big-endian signed int
                        sensor_data[sensor_type] = {
                            'value': value,
                            'unit': config.get('unit', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
        
        return sensor_data if sensor_data else None
    
    def _read_schneider_sensor_data(self, client: SchneiderModiconClient, sensor_config: Dict) -> Optional[Dict]:
        """Read sensor data from Schneider PLC"""
        sensor_data = {}
        
        for sensor_type, config in sensor_config.items():
            if 'address' in config:
                address = config['address']
                data_type = config.get('data_type', 'holding_register')
                scale_factor = config.get('scale_factor', 1.0)
                
                if data_type == 'holding_register':
                    values = client.read_holding_registers(address, 1)
                    if values:
                        value = values[0] * scale_factor
                        sensor_data[sensor_type] = {
                            'value': value,
                            'unit': config.get('unit', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                elif data_type == 'holding_register_float':
                    # Read 2 registers for 32-bit float
                    values = client.read_holding_registers(address, 2)
                    if values and len(values) == 2:
                        # Combine two 16-bit registers into 32-bit float
                        combined = (values[0] << 16) | values[1]
                        value = struct.unpack('>f', struct.pack('>I', combined))[0]
                        sensor_data[sensor_type] = {
                            'value': value,
                            'unit': config.get('unit', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
        
        return sensor_data if sensor_data else None
    
    def write_alert_to_plc(self, factory_id: str, alert_data: Dict) -> bool:
        """Write alert information to PLC"""
        if factory_id not in self.active_connections:
            return False
        
        connection = self.active_connections[factory_id]
        client = connection['client']
        
        try:
            if connection['type'] == 'siemens':
                return self._write_siemens_alert(client, alert_data)
            elif connection['type'] == 'schneider':
                return self._write_schneider_alert(client, alert_data)
        except Exception as e:
            logger.error(f"Error writing alert to PLC: {str(e)}")
            return False
    
    def _write_siemens_alert(self, client: SiemensS7Client, alert_data: Dict) -> bool:
        """Write alert to Siemens PLC"""
        # Example: Write alert status to specific DB
        db_number = 100  # Alert DB
        address = 0      # Alert status address
        
        # Convert severity to numeric value
        severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        severity_value = severity_map.get(alert_data.get('severity', 'low'), 1)
        
        # Pack alert data
        alert_bytes = struct.pack('>HH', 1, severity_value)  # Alert active, severity
        
        return client.write_db(db_number, address, alert_bytes)
    
    def _write_schneider_alert(self, client: SchneiderModiconClient, alert_data: Dict) -> bool:
        """Write alert to Schneider PLC"""
        # Example: Write alert status to holding registers
        alert_register = 1000  # Alert status register
        severity_register = 1001  # Alert severity register
        
        # Convert severity to numeric value
        severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        severity_value = severity_map.get(alert_data.get('severity', 'low'), 1)
        
        # Write alert active status
        if not client.write_single_register(alert_register, 1):
            return False
        
        # Write alert severity
        return client.write_single_register(severity_register, severity_value)
    
    def get_connection_status(self) -> Dict[str, Dict]:
        """Get status of all PLC connections"""
        status = {}
        
        for factory_id, connection in self.active_connections.items():
            status[factory_id] = {
                'type': connection['type'],
                'connected': True,
                'connected_at': connection['connected_at'].isoformat(),
                'last_communication': datetime.utcnow().isoformat()
            }
        
        return status
    
    def test_plc_communication(self, factory_id: str) -> Dict[str, Any]:
        """Test PLC communication"""
        if factory_id not in self.active_connections:
            return {'success': False, 'message': 'Not connected to PLC'}
        
        connection = self.active_connections[factory_id]
        client = connection['client']
        
        try:
            if connection['type'] == 'siemens':
                # Test read from a known DB
                test_data = client.read_db(1, 0, 4)  # Read 4 bytes from DB1
                success = test_data is not None
            elif connection['type'] == 'schneider':
                # Test read from holding registers
                test_data = client.read_holding_registers(0, 1)  # Read 1 register
                success = test_data is not None
            else:
                success = False
            
            return {
                'success': success,
                'message': 'Communication test successful' if success else 'Communication test failed',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Communication test failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }

# Global PLC integration service instance
plc_service = PLCIntegrationService()

