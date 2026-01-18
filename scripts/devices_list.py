from AvtpCanManager import AvtpCanManager
import cantools
from typing import Dict, Any
import socket
import struct
import time
import sys
from pathlib import Path

# Add parent directory to path to import from sdrig package
sys.path.insert(0, str(Path(__file__).parent.parent))
from sdrig.protocol.can_protocol import normalize_can_id_for_dbc

class CanMessageHandler:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        self.devices: Dict[str, Dict[str, Any]] = {}

    def is_j1939(self,can_id: int) -> bool:
        return can_id > 0x7FF  # extended frame with J1939-like structure

    def extract_pgn(self,can_id: int) -> int:
        # PGN: bits 8–25
        return (can_id >> 8) & 0x3FFFF

    def print_devices(self):
        
        print(f"Devices found: {len(self.devices)}")
        for device in self.devices:
            ip_addr = ""
            app_name = ""
            app_version = ""
            app_build_date = ""
            hw_name = ""
            print("|-------------------------------------------------------------------|")
            # print(f"Device: {device}")
            if "MODULE_INFO" in self.devices[device]:
                module_info_msg = self.devices[device]['MODULE_INFO']
                if "module_app_fw_name_1" in module_info_msg:
                    fw_name_1 = module_info_msg['module_app_fw_name_1'].to_bytes(8, 'little').decode('utf-8')
                    fw_name_2 = module_info_msg['module_app_fw_name_2'].to_bytes(8, 'little').decode('utf-8')
                    fw_name_3 = module_info_msg['module_app_fw_name_3'].to_bytes(8, 'little').decode('utf-8')
                    fw_name = fw_name_1 + fw_name_2 + fw_name_3
                    app_name = fw_name.rstrip("\x00")

                    app_version = f"{module_info_msg['module_app_ver_gen']}." \
                                    f"{module_info_msg['module_app_ver_major']}." \
                                    f"{module_info_msg['module_app_ver_minor']}." \
                                    f"{module_info_msg['module_app_ver_fix']}." \
                                    f"{module_info_msg['module_app_ver_build']}"
                    app_version = f"{app_version} {module_info_msg['module_app_target']}"

                    app_build_date = f"{module_info_msg['module_app_build_day']:02d}/" \
                                    f"{module_info_msg['module_app_build_month']:02d}/" \
                                    f"{module_info_msg['module_app_build_year']:04d} " \
                                    f"{module_info_msg['module_app_build_hour']:02d}:" \
                                    f"{module_info_msg['module_app_build_min']:02d}"
                    app_crc = f"{module_info_msg['module_app_crc']:08X}"

                if "module_app_hw_name_1" in self.devices[device]["MODULE_INFO"]:
                    hw_name_1 = module_info_msg['module_app_hw_name_1'].to_bytes(8, 'little').decode('utf-8')
                    hw_name_2 = module_info_msg['module_app_hw_name_2'].to_bytes(8, 'little').decode('utf-8')
                    hw_name = hw_name_1 + hw_name_2
                    hw_name = hw_name.rstrip("\x00")

            if "MODULE_INFO_EX" in self.devices[device]:
                module_info_ex_msg = self.devices[device]['MODULE_INFO_EX']
                if "module_ip_addr" in module_info_ex_msg:
                    ip_addr = module_info_ex_msg['module_ip_addr'].to_bytes(4, 'big') 
                    #decode the bytes to string
                    ip_addr = socket.inet_ntoa(ip_addr)
                    # print(f"IP Address: {ip_addr}")

            if ip_addr != "" and app_name != "" and hw_name != "":
                print(f"Device Name   | {app_name}")
                print(f"Device HW     | {hw_name}")
                print(f"Device Version| {app_version} | {app_build_date} | {app_crc}")
                print(f"MAC Address   | {device}")
                print(f"IP Address    | {ip_addr}")


    def parse_acf_can_message(self, message, mac_addr_str):
      
        # Extract the ACF CAN Brief fields
        #message type located in byte 0 bits[1-7]
        #message length located in byte 1 bits[0-7] and byte 0 bits[0]
        #flags located in byte 2 bits[0-7]
        #flag is CAN FD located in byte 2 bits[1]
        #bus id located in byte 3 bits[0-4]
        #frame length located in byte 8 bits[0-7]
        #can id located in byte 4 bits [0-4] bytes 5-7 bits[0-7]
        message_type = (message[0] >> 1) & 0x7F
        message_length_quadlets = ((message[0] & 0x01) << 8) | (message[1] & 0xFF)
        flags = (message[2] ) & 0xFF
        flag_is_can_fd = (message[2] >> 1) & 0x01
        bus_id = (message[3] ) & 0x1F
        frame_length = (message_length_quadlets * 4 ) - 8
        can_id = ((message[4] & 0x1F) << 24) | (message[5] << 16) | (message[6] << 8) | (message[7] & 0xFF)
        can_id = normalize_can_id_for_dbc(can_id)
        data = message[8:(message_length_quadlets * 4 )]
        des_message = {}
        if bus_id == 0 :
            #decode the message
            des_message = self.db.decode_message(can_id, data)
            # Display the parsed data
            #print(f"CAN Brief: Type={message_type}, Is CANFD={flag_is_can_fd}, Length={frame_length}, Bus ID={bus_id}, CAN ID={can_id:08x}, Data={data.hex()}")
            #get the message with the can id
            #if message is MODULE_INFO_EX
            if can_id == 0x0C08FEFE:
                #create devices[mac_addr].MODULE_INFO_EX
                #chek if devices hax member mac_addr
                if mac_addr_str not in self.devices:
                    self.devices[mac_addr_str] = {}
                self.devices[mac_addr_str]['MODULE_INFO_EX'] = des_message
                # module_mac_addr = des_message['module_mac_addr']
                # module_chip_uid_1 = des_message['module_chip_uid_1']
                # module_chip_uid_2 = des_message['module_chip_uid_2']
                # module_ip_addr = des_message['module_ip_addr']

            #if message is MODULE_INFO
            if can_id == 0x0C01FEFE:
                if mac_addr_str not in self.devices:
                    self.devices[mac_addr_str] = {}
                self.devices[mac_addr_str]['MODULE_INFO'] = des_message
            
            #if message is MODULE_INFO_BOOT
            if can_id == 0x0c02feFE:
                if mac_addr_str not in self.devices:
                    self.devices[mac_addr_str] = {}
                self.devices[mac_addr_str]['MODULE_INFO_BOOT'] = des_message

            #if message is PIN_INFO
            if can_id == 0x0c10fefe:
                if mac_addr_str not in self.devices:
                    self.devices[mac_addr_str] = {}
                self.devices[mac_addr_str]['PIN_INFO'] = des_message


    def parse_avtp_frame(self,frame):
        frame = bytes(frame)
        # Skip the Ethernet header (14 bytes) and AVTP common headers (12 bytes)
        offset = 26
        #src mac located in bytes 0-5
        #dst mac located in bytes 6-11
        #ethernet type located in bytes 12-13
        #avtp subtype located in byte 14 bits[0-7]
        #avtp version located in byte 15 bits[0-2]
        #data length located in byte 15 bits[0-2] and byte 16 bits[0-7]
        #sequence number located in byte 17 bits[0-7]
        #stream id located in bytes 18-25
        dst_mac = frame[0:6]
        src_mac = frame[6:12]
        ethernet_type = (frame[12] << 8) | (frame[13] & 0xFF)
        avtp_subtype = (frame[14] ) & 0xFF
        avtp_version = (frame[15] ) & 0x07
        data_length = ((frame[15] & 0x07) << 8) | (frame[16] & 0xFF)
        sequence_num = (frame[17] ) & 0xFF
        stream_id = ((frame[18] & 0xFF) << 56) | ((frame[19] & 0xFF) << 48) | ((frame[20] & 0xFF) << 40) | ((frame[21] & 0xFF) << 32) | ((frame[22] & 0xFF) << 24) | ((frame[23] & 0xFF) << 16) | ((frame[24] & 0xFF) << 8) | (frame[25] & 0xFF)

        src_mac_str = ':'.join('{:02x}'.format(x) for x in src_mac)
        
        # Check if it is a Non-Time-Synchronous Control Format message
        if avtp_subtype == 0x82 and ethernet_type == 0x22F0:
            #print(f"AVTP Frame: Subtype={avtp_subtype}, Version={avtp_version}, Seq={sequence_num}, Stream ID={stream_id}")
            #get mac address of the device in form of string xx:xx:xx:xx:xx:xx

            # Process each ACF-CAN message in the AVTP frame
            while offset < (data_length+26):
                # The first two bytes of each ACF-CAN message contain the message type and length
                acf_header = struct.unpack_from('!H', frame, offset)[0]
                message_length_quadlets = acf_header & 0xFF
                message_length_bytes = message_length_quadlets * 4

                # Extract the ACF-CAN message
                acf_can_message = frame[offset:offset + message_length_bytes]
                self.parse_acf_can_message(acf_can_message,src_mac_str)

                # Move to the next message
                offset += message_length_bytes




if __name__ == "__main__":
    handler = CanMessageHandler('soda_xil_fd.dbc')
    manager = AvtpCanManager(iface="enp0s31f6", stream_id=1)
    manager.start_receiving(handler.parse_avtp_frame)
    acf_can_bus_id = int(0)
    acf_can_id = int(0x0400fffe)
    acf_can_data =  bytes(b'\x1f\x00\x00\x00\x00\x00\x00\x00')

    for _i in range(3):
        manager.send_can_message(acf_can_bus_id, acf_can_id, acf_can_data, True, True,"FF:FF:FF:FF:FF:FF")
        time.sleep(0.05)
    

    try:
        while True:
            manager.send_can_message(acf_can_bus_id, acf_can_id, acf_can_data, True, True,"FF:FF:FF:FF:FF:FF")
            handler.print_devices()
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_receiving()                