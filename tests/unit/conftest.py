"""
Pytest fixtures for unit tests

Provides mocks and fixtures for testing without hardware.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import cantools


@pytest.fixture
def mock_can_db():
    """Mock CAN database"""
    db = Mock(spec=cantools.database.Database)

    # Mock encode_message
    def encode_message(can_id, data):
        # Simple mock: convert dict to bytes
        return bytes([len(data)] + list(range(len(data))))

    # Mock decode_message
    def decode_message(can_id, data):
        # Simple mock: return empty dict
        return {}

    db.encode_message = Mock(side_effect=encode_message)
    db.decode_message = Mock(side_effect=decode_message)
    db.get_message_by_name = Mock(return_value=Mock(frame_id=0x123))

    return db


@pytest.fixture
def mock_avtp_manager():
    """Mock AVTP manager"""
    manager = Mock()
    manager.send_can_message = Mock()
    manager.start_listening = Mock()
    manager.stop_listening = Mock()
    manager.close = Mock()
    return manager


@pytest.fixture
def mock_task_monitor():
    """Mock task monitor"""
    monitor = Mock()
    monitor.add_task_sec = Mock()
    monitor.add_task_ms = Mock()
    monitor.start = Mock()
    monitor.stop = Mock()
    monitor.tasks = {}
    return monitor


@pytest.fixture
def uio_device_mocks(mock_can_db, mock_avtp_manager, mock_task_monitor):
    """Mocks for UIO device"""
    with patch('sdrig.protocol.can_messages.cantools.database.load_file', return_value=mock_can_db), \
         patch('sdrig.devices.device_sdr.AvtpCanManager', return_value=mock_avtp_manager), \
         patch('sdrig.devices.device_sdr.TaskMonitor', return_value=mock_task_monitor), \
         patch('sdrig.devices.device_sdr.CANMessageDatabase', return_value=Mock()):
        yield {
            'can_db': mock_can_db,
            'avtp_manager': mock_avtp_manager,
            'task_monitor': mock_task_monitor
        }


@pytest.fixture
def eload_device_mocks(mock_can_db, mock_avtp_manager, mock_task_monitor):
    """Mocks for ELoad device"""
    with patch('sdrig.protocol.can_messages.cantools.database.load_file', return_value=mock_can_db), \
         patch('sdrig.devices.device_sdr.AvtpCanManager', return_value=mock_avtp_manager), \
         patch('sdrig.devices.device_sdr.TaskMonitor', return_value=mock_task_monitor), \
         patch('sdrig.devices.device_sdr.CANMessageDatabase', return_value=Mock()):
        yield {
            'can_db': mock_can_db,
            'avtp_manager': mock_avtp_manager,
            'task_monitor': mock_task_monitor
        }


@pytest.fixture
def sample_module_info():
    """Sample MODULE_INFO message data"""
    return {
        'sys_runtime_s': 1000,
        'module_status': 3,
        'module_app_ver_major': 1,
        'module_app_ver_minor': 2,
        'module_app_ver_fix': 3,
        'module_app_fw_name_1': ord('U'),
        'module_app_fw_name_2': ord('I'),
        'module_app_fw_name_3': ord('O'),
    }


@pytest.fixture
def sample_voltage_data():
    """Sample voltage measurement data"""
    return {
        f'vlt_i_{i}_value': 12.0 + i * 0.5
        for i in range(1, 9)
    }


@pytest.fixture
def sample_current_data():
    """Sample current measurement data"""
    return {
        f'cur_i_{i}_value': 2.5 + i * 0.1
        for i in range(1, 9)
    }


@pytest.fixture
def sample_pwm_data():
    """Sample PWM measurement data"""
    data = {}
    for i in range(1, 9):
        data[f'icu_{i}_frequency'] = 1000.0 + i * 100
        data[f'icu_{i}_duty'] = 50.0 + i * 5
    return data
