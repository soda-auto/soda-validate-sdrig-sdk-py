"""
DeviceIfMux - Interface Multiplexer Device

This module provides the DeviceIfMux class for controlling CAN/LIN interface
multiplexer modules with 8 CAN channels and optional LIN support.
"""

from typing import List, Dict, Optional, Callable
from ..devices.device_sdr import DeviceSDR
from ..types.enums import DeviceType, PGN, CANSpeed, CANState, LastErrorCode
from ..types.structs import CANChannelState
from ..utils.logger import get_logger

logger = get_logger('device_ifmux')


class CANChannel:
    """
    Represents a single CAN channel

    Supports:
    - CAN FD (up to 5Mbps)
    - Speed configuration
    - State monitoring
    - Internal/external relay control
    - Raw message routing
    """

    def __init__(self, device: 'DeviceIfMux', channel_id: int):
        """
        Initialize CAN channel

        Args:
            device: Parent IfMux device
            channel_id: Channel number (0-7)
        """
        self.device = device
        self.channel_id = channel_id
        self.state = CANChannelState(channel_id=channel_id)

    def set_speed(self, speed: CANSpeed):
        """
        Set CAN bus speed

        Args:
            speed: CAN speed enum
        """
        # Map CAN speed values to classic and FD fields
        # Classic speeds: 0=OFF, 1=250K, 2=500K, 3=1M
        # FD speeds: 0=OFF, 1=1M, 2=2M, 3=4M, 4=5M, 5=8M
        if speed.value >= 1000000:  # CAN FD speeds
            self.device._can_speeds[self.channel_id] = 0  # Disable classic
            if speed.value == 1000000:
                self.device._can_speeds_fd[self.channel_id] = 1
            elif speed.value == 2000000:
                self.device._can_speeds_fd[self.channel_id] = 2
            elif speed.value == 4000000:
                self.device._can_speeds_fd[self.channel_id] = 3
            elif speed.value == 5000000:
                self.device._can_speeds_fd[self.channel_id] = 4
            elif speed.value == 8000000:
                self.device._can_speeds_fd[self.channel_id] = 5
        else:  # Classic CAN speeds
            self.device._can_speeds_fd[self.channel_id] = 0  # Disable FD
            if speed.value == 250000:
                self.device._can_speeds[self.channel_id] = 1
            elif speed.value == 500000:
                self.device._can_speeds[self.channel_id] = 2
            elif speed.value == 1000000:
                self.device._can_speeds[self.channel_id] = 3
            else:
                self.device._can_speeds[self.channel_id] = 0  # OFF

        self.state.speed = speed.value
        logger.debug(f"Channel {self.channel_id}: Set speed to {speed.value} bps")

        # Send immediately if value changed (Performance optimization - change detection)
        if (self.device._can_speeds != self.device._can_speeds_last or
            self.device._can_speeds_fd != self.device._can_speeds_fd_last):
            self.device._send_can_info_req()

    def get_state(self) -> CANState:
        """
        Get CAN controller state

        Returns:
            CAN state
        """
        return self.state.state

    def get_lec(self) -> LastErrorCode:
        """
        Get last error code

        Returns:
            Last error code
        """
        return self.state.lec

    def get_stats(self) -> Dict:
        """
        Get channel statistics

        Returns:
            Dictionary with tx_count, rx_count, error_count
        """
        return {
            'tx_count': self.state.tx_count,
            'rx_count': self.state.rx_count,
            'error_count': self.state.error_count,
            'state': self.state.state.name,
            'lec': self.state.lec.name
        }

    def set_internal_relay(self, closed: bool):
        """
        Set internal relay state

        Args:
            closed: True to close relay, False to open
        """
        # Update internal relay state
        self.device._can_mux_int[self.channel_id] = 1 if closed else 0
        logger.debug(f"Channel {self.channel_id}: Internal relay {'closed' if closed else 'open'}")

        # Send CAN_MUX_REQ with all relay states
        self.device._send_can_mux_req()

    def set_external_relay(self, output: int, closed: bool):
        """
        Set external relay matrix output

        Args:
            output: External output number (0-7)
            closed: True to close relay, False to open
        """
        if not 0 <= output <= 7:
            raise ValueError(f"External output must be 0-7, got {output}")

        # Update external relay bitmask
        if closed:
            self.device._can_mux_ext[self.channel_id] |= (1 << output)
        else:
            self.device._can_mux_ext[self.channel_id] &= ~(1 << output)

        logger.debug(
            f"Channel {self.channel_id}: External relay {output} "
            f"{'closed' if closed else 'open'}"
        )

        # Send CAN_MUX_REQ with all relay states
        self.device._send_can_mux_req()

    def __repr__(self) -> str:
        return (
            f"CANChannel({self.channel_id}, "
            f"state={self.state.state.name}, "
            f"speed={self.state.speed})"
        )


class DeviceIfMux(DeviceSDR):
    """
    Interface Multiplexer Device

    Provides control for 8 CAN channels with FD support and optional LIN.
    """

    def __init__(
        self,
        mac_address: str,
        iface: str,
        stream_id: int,
        dbc_path: str,
        lin_enabled: bool = False
    ):
        """
        Initialize IfMux device

        Args:
            mac_address: Device MAC address
            iface: Network interface name
            stream_id: AVTP stream ID
            dbc_path: Path to DBC file
            lin_enabled: Enable LIN support
        """
        super().__init__(mac_address, iface, stream_id, dbc_path)

        # Create 8 CAN channels
        self.channels: List[CANChannel] = [CANChannel(self, i) for i in range(8)]

        # CAN speeds for all channels (for sending in one message)
        self._can_speeds = [0] * 8  # CAN classic speeds (0 = not configured)
        self._can_speeds_fd = [0] * 8  # CAN FD speeds (0 = not configured)

        # Last sent speeds for change detection (Performance optimization)
        self._can_speeds_last = [0] * 8
        self._can_speeds_fd_last = [0] * 8

        # CAN MUX relay states
        self._can_mux_int = [0] * 8  # Internal relay enable (0 or 1)
        self._can_mux_ext = [0] * 8  # External relay output bitmask (0-255)

        # LIN support
        self.lin_enabled = lin_enabled

        # Raw CAN message callback
        self._raw_can_callback: Optional[Callable[[int, int, bytes], None]] = None

        logger.info(f"IfMux device initialized: {mac_address} (LIN: {lin_enabled})")

    def device_type(self) -> DeviceType:
        """Get device type"""
        return DeviceType.IFMUX

    def channel(self, channel_id: int) -> CANChannel:
        """
        Get channel by ID

        Args:
            channel_id: Channel ID (0-7)

        Returns:
            CANChannel object

        Raises:
            ValueError: If channel ID invalid
        """
        if not 0 <= channel_id <= 7:
            raise ValueError(f"Channel ID must be 0-7, got {channel_id}")
        return self.channels[channel_id]

    def send_raw_can(
        self,
        channel_id: int,
        can_id: int,
        data: bytes,
        extended: bool = True,
        fd: bool = True
    ):
        """
        Send raw CAN message on specified channel

        Args:
            channel_id: CAN channel (0-7)
            can_id: CAN message ID
            data: Message data
            extended: Use extended ID
            fd: Use CAN-FD
        """
        if not 0 <= channel_id <= 7:
            raise ValueError(f"Channel ID must be 0-7, got {channel_id}")

        # Send raw CAN via AVTP
        self.avtp_manager.send_can_message(
            can_bus_id=channel_id+1,  # Bus IDs are 1-8
            msg_id=can_id,
            data=data,
            extended_id=extended,
            can_fd=fd,
            dst_mac=self.mac_address
        )

        logger.debug(
            f"Sent raw CAN on channel {channel_id}: "
            f"ID=0x{can_id:X}, len={len(data)}"
        )

    def register_raw_can_callback(
        self,
        callback: Callable[[int, int, bytes], None]
    ):
        """
        Register callback for raw CAN messages

        Args:
            callback: Function(channel_id, can_id, data)
        """
        self._raw_can_callback = callback

    def _send_can_info_req(self):
        """Send CAN_INFO_REQ with speed configuration for all channels"""
        data = {}
        for i in range(1, 9):
            # Each channel needs two fields: classic speed and FD speed
            data[f"can{i}_speed"] = self._can_speeds[i - 1]
            data[f"can{i}_speed_fd"] = self._can_speeds_fd[i - 1]

        try:
            self.send_can_message(PGN.CAN_INFO_REQ, data)
            # Update last sent values for change detection (Performance optimization)
            self._can_speeds_last = self._can_speeds.copy()
            self._can_speeds_fd_last = self._can_speeds_fd.copy()
        except Exception as e:
            logger.debug(f"Failed to send CAN_INFO_REQ: {e}")

    def _send_can_mux_req(self):
        """Send CAN_MUX_REQ with relay configuration for all channels"""
        data = {}
        for i in range(1, 9):
            # Each channel needs two fields: internal relay and external relay
            data[f"can_mux_int_can{i}_en"] = self._can_mux_int[i - 1]
            data[f"can_mux_ext_can{i}_out"] = self._can_mux_ext[i - 1]

        try:
            self.send_can_message(PGN.CAN_MUX_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to send CAN_MUX_REQ: {e}")

    def configure_lin_frame(
        self,
        frame_id: int,
        data_length: int,
        checksum_type: int = 1,
        direction: int = 1  # 0=receive, 1=transmit
    ):
        """
        Configure LIN frame (if LIN enabled)

        Args:
            frame_id: LIN frame ID (0-61)
            data_length: Data length (1-8)
            checksum_type: Checksum type (0=classic, 1=enhanced)
            direction: Direction (0=receive, 1=transmit)
        """
        if not self.lin_enabled:
            raise RuntimeError("LIN not enabled for this device")

        if not 0 <= frame_id <= 61:
            raise ValueError(f"LIN frame ID must be 0-61, got {frame_id}")
        if not 1 <= data_length <= 8:
            raise ValueError(f"LIN data length must be 1-8, got {data_length}")

        # Build data with all frame configurations (default all disabled)
        data = {}
        for fid in range(62):  # 0-61
            data[f"lin_cfg_frm{fid}_enable"] = 1 if fid == frame_id else 0
            data[f"lin_cfg_frm{fid}_dir_transmit"] = direction if fid == frame_id else 0
            data[f"lin_cfg_frm{fid}_cst_classic"] = checksum_type if fid == frame_id else 0
            data[f"lin_cfg_frm{fid}_len"] = data_length if fid == frame_id else 1

        try:
            self.send_can_message(PGN.LIN_CFG_REQ, data)
            logger.debug(f"Configured LIN frame {frame_id}")
        except Exception as e:
            logger.debug(f"Failed to configure LIN frame {frame_id}: {e}")

    def send_lin_frame(self, frame_id: int, data: bytes):
        """
        Send LIN frame (if LIN enabled)

        Args:
            frame_id: LIN frame ID
            data: Frame data (1-8 bytes)
        """
        if not self.lin_enabled:
            raise RuntimeError("LIN not enabled for this device")

        if not 0 <= frame_id <= 61:
            raise ValueError(f"LIN frame ID must be 0-61, got {frame_id}")
        if not 1 <= len(data) <= 8:
            raise ValueError(f"LIN data must be 1-8 bytes, got {len(data)}")

        # Build message with frame ID and data bytes
        msg_data = {"lin_frame_id": frame_id}
        for i in range(8):
            msg_data[f"lin_frame_data{i}"] = data[i] if i < len(data) else 0

        try:
            self.send_can_message(PGN.LIN_FRAME_SET_REQ, msg_data)
            logger.debug(f"Sent LIN frame {frame_id}")
        except Exception as e:
            logger.debug(f"Failed to send LIN frame {frame_id}: {e}")

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for IfMux device"""
        # Request MODULE_INFO every 5 seconds as keepalive
        self.request_module_info()
        self.task_monitor.add_task_sec(
            "module_info",
            self.request_module_info,
            5.0
        )

        # Request CAN states every 2 seconds
        self.task_monitor.add_task_sec(
            "can_states",
            self._request_can_states,
            2.0
        )

    def _request_can_states(self):
        """Request CAN channel states"""
        # Send CAN_INFO_REQ with current speeds (device will respond with CAN_INFO_ANS)
        data = {}
        for i in range(1, 9):
            # Each channel needs two fields: classic speed and FD speed
            data[f"can{i}_speed"] = self._can_speeds[i - 1]
            data[f"can{i}_speed_fd"] = self._can_speeds_fd[i - 1]

        try:
            self.send_can_message(PGN.CAN_INFO_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to request CAN states: {e}")

    def _parse_acf_can_message(self, message: bytes, src_mac: str):
        """
        Parse ACF-CAN message and handle raw CAN callback

        Override parent method to extract channel_id and can_id for raw CAN callback
        before processing through DBC

        Args:
            message: ACF-CAN message bytes
            src_mac: Source MAC address
        """
        if len(message) < 8:
            return

        # Extract fields from ACF-CAN message
        message_type = (message[0] >> 1) & 0x7F
        message_length_quadlets = ((message[0] & 0x01) << 8) | message[1]
        bus_id = message[3] & 0x1F
        frame_length = (message_length_quadlets * 4) - 8
        can_id = ((message[4] & 0x1F) << 24) | (message[5] << 16) | (message[6] << 8) | message[7]
        data = message[8:8 + frame_length]

        # Check if this is a raw CAN message (not a system message)
        # System messages have bus_id=0 and use J1939 PGN format
        from ..protocol.can_protocol import extract_pgn
        pgn = extract_pgn(can_id)

        # Determine if this is a raw CAN message or system message
        # System messages use specific PGNs, raw messages use other CAN IDs
        system_pgns = {
            PGN.MODULE_INFO.value,
            PGN.MODULE_INFO_EX.value,
            PGN.CAN_INFO_ANS.value,
            PGN.CAN_STATE_ANS.value,
            PGN.CAN_MUX_ANS.value,
            PGN.LIN_FRAME_RCVD_ANS.value if self.lin_enabled else None
        }

        is_system_message = (bus_id == 0 and pgn in system_pgns)

        # If raw CAN callback is registered and this is not a system message, call it
        if self._raw_can_callback and not is_system_message:
            try:
                self._raw_can_callback(bus_id, can_id, data)
                logger.debug(
                    f"Raw CAN callback: channel={bus_id}, "
                    f"ID=0x{can_id:08X}, len={len(data)}"
                )
            except Exception as e:
                logger.error(f"Error in raw CAN callback: {e}")

        # Call parent implementation for system message processing
        super()._parse_acf_can_message(message, src_mac)

    def _process_can_message(self, pgn: int, data: bytes, src_mac: str):
        """
        Process received CAN message

        Args:
            pgn: Parameter Group Number
            data: Message data
            src_mac: Source MAC address
        """
        try:
            # Build 29-bit CAN ID with priority=3 and SA=0x00 for DBC lookup
            # Extended bit handled by DBC layer
            can_id = (3 << 26) | (pgn << 8) | 0x00
            decoded = self.can_db.decode_message(can_id, data)

            # Handle different message types
            if pgn == PGN.MODULE_INFO.value:
                self._handle_module_info(decoded)
            elif pgn == PGN.MODULE_INFO_EX.value:
                self._handle_module_info_ex(decoded)
            elif pgn == PGN.CAN_INFO_ANS.value:
                self._handle_can_info(decoded)
            elif pgn == PGN.CAN_STATE_ANS.value:
                self._handle_can_state(decoded)
            elif pgn == PGN.CAN_MUX_ANS.value:
                self._handle_can_mux(decoded)
            elif pgn == PGN.LIN_FRAME_RCVD_ANS.value and self.lin_enabled:
                self._handle_lin_frame(decoded)
            else:
                # Raw CAN message routing
                if self._raw_can_callback:
                    # Extract channel from message
                    # (implementation depends on message format)
                    pass

        except Exception as e:
            logger.debug(f"Error processing IfMux message PGN 0x{pgn:04X}: {e}")

    def _handle_module_info(self, decoded: Dict):
        """Handle MODULE_INFO message"""
        from ..protocol.can_messages import ModuleInfoMessage
        self.module_info = ModuleInfoMessage.from_decoded(decoded, self.mac_address)
        logger.info(f"IfMux Module: {self.module_info.app_name} {self.module_info.version}")

    def _handle_module_info_ex(self, decoded: Dict):
        """Handle MODULE_INFO_EX message"""
        from ..protocol.can_messages import ModuleInfoExMessage
        info_ex = ModuleInfoExMessage.from_decoded(decoded, self.mac_address)
        if self.module_info:
            self.module_info.ip_address = info_ex.ip_address
            self.module_info.chip_uid = info_ex.chip_uid
        logger.info(f"IfMux IP: {info_ex.ip_address}")

    def _handle_can_info(self, decoded: Dict):
        """Handle CAN_INFO_ANS message"""
        channel_id = decoded.get("channel_id", 0)
        if 0 <= channel_id <= 7:
            speed = decoded.get("speed", 0)
            self.channels[channel_id].state.speed = speed

    def _handle_can_state(self, decoded: Dict):
        """Handle CAN_STATE_ANS message"""
        channel_id = decoded.get("channel_id", 0)
        if 0 <= channel_id <= 7:
            state = decoded.get("state", 0)
            lec = decoded.get("lec", 0)
            tx_count = decoded.get("tx_count", 0)
            rx_count = decoded.get("rx_count", 0)
            error_count = decoded.get("error_count", 0)

            channel = self.channels[channel_id]
            try:
                channel.state.state = CANState(state)
                channel.state.lec = LastErrorCode(lec)
            except ValueError:
                pass

            channel.state.tx_count = tx_count
            channel.state.rx_count = rx_count
            channel.state.error_count = error_count

    def _handle_can_mux(self, decoded: Dict):
        """Handle CAN_MUX_ANS message"""
        logger.debug(f"CAN MUX response: {decoded}")

    def _handle_lin_frame(self, decoded: Dict):
        """Handle LIN_FRAME_RCVD_ANS message"""
        frame_id = decoded.get("frame_id", 0)
        data = decoded.get("data", b'')
        logger.debug(f"Received LIN frame {frame_id}: {data.hex()}")

    def __repr__(self) -> str:
        return (
            f"DeviceIfMux(mac={self.mac_address}, "
            f"channels=8, lin={self.lin_enabled}, "
            f"running={self._running})"
        )
