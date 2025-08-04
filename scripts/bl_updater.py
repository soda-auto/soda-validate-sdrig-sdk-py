import os
import socket
import struct
import time
import threading
from scapy.all import Ether, sendp, sniff, AsyncSniffer
import cantools
import tftpy
import argparse


# Constants for Ethernet
ETH_P_ALL = 3
BROADCAST_MAC = 'ff:ff:ff:ff:ff:ff'
stop_sniffing = False
#cur dir
cur_dir = os.getcwd()
UIO_Path = ""
ELM_Path = ""
IfMux_Path = ""
RDO_Path = ""
Cmds_Path = "./commands/"
#load the dbc file
db = cantools.database.load_file('soda_xil_fd.dbc')
#init devices dictionary as list
devices = {}


class cmd:
    DELETE_APP1 = 0
    DELETE_APP2 = 1
    DELETE_APP3 = 2
    SELECT_APP1 = 3
    SELECT_APP2 = 4
    SELECT_APP3 = 5
    INSTALL_BL  = 6


def find_cmd(command_num: int) -> str:
    commands = {
        cmd.SELECT_APP1: "command_select_app1.bin",
        cmd.SELECT_APP2: "command_select_app2.bin",
        cmd.SELECT_APP3: "command_select_app3.bin",
        cmd.DELETE_APP1: "command_delete_app1.bin",
        cmd.DELETE_APP2: "command_delete_app2.bin",
        cmd.DELETE_APP3: "command_delete_app3.bin",
        cmd.INSTALL_BL:  "command_install_bl_fw.bin",
    }
    return commands.get(command_num, "ERROR")


def find_files_which_end(dir, endings):
    directory = cur_dir
    if dir == "SODA.HIL.UIO":
        directory = UIO_Path
    elif dir == "SODA.HIL.ELM":
        directory = ELM_Path
    elif dir == "SODA.HIL.IFMUX":
        directory = IfMux_Path
    elif dir == "SODA.SDR.RDO":
        directory = RDO_Path
    
    # Check if the specified directory exists
    if not os.path.exists(directory):
        print(f"Directory {directory} not found.")
        return None

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(endings):
            return os.path.join(directory, filename)

    return None


def upload_file(server_ip, local_file_path, remote_file_path) -> bool:
    result = True
    try:
        if server_ip == "0.0.0.0":
            raise ConnectionError("Module is not yet ready to work on TCP. Wait for a bit (10s).")
        client = tftpy.TftpClient(server_ip)
        client.upload(remote_file_path, local_file_path)
        print(f"File {local_file_path} successfully uploaded to {server_ip}")

    except Exception as e:
        print(f"Failed to upload file: {e}")
        result = False
    return result


def print_devices():
    global devices
    print(f"Devices found: {len(devices)}")
    for device in devices:
        ip_addr = ""
        app_name = ""
        app_version = ""
        app_build_date = ""
        hw_name = ""
        print("|-------------------------------------------------------------------|")
        # print(f"Device: {device}")
        if "MODULE_INFO" in devices[device]:
            module_info_msg = devices[device]['MODULE_INFO']
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

            if "module_app_hw_name_1" in devices[device]["MODULE_INFO"]:
                hw_name_1 = module_info_msg['module_app_hw_name_1'].to_bytes(8, 'little').decode('utf-8')
                hw_name_2 = module_info_msg['module_app_hw_name_2'].to_bytes(8, 'little').decode('utf-8')
                hw_name = hw_name_1 + hw_name_2

        if "MODULE_INFO_EX" in devices[device]:
            module_info_ex_msg = devices[device]['MODULE_INFO_EX']
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

            #find file with the name contains **firmware.bin in folder app_name
            # firmware_file_name = find_files_which_end(app_name, 'bin')
            firmware_file_name = None
            is_bootloader: bool = False
            if "BOOT" in app_name:
                is_bootloader = True
            if not is_bootloader:
                if app_name == "SODA.HIL.UIO" and UIO_Path != "":
                    firmware_file_name = UIO_Path
                elif app_name == "SODA.HIL.ELM" and ELM_Path != "":
                    firmware_file_name = ELM_Path
                elif app_name == "SODA.HIL.IFMUX" and IfMux_Path != "":
                    firmware_file_name = IfMux_Path
                elif app_name == "SODA.SDR.RDO" and RDO_Path != "":
                    firmware_file_name = RDO_Path
            else:
                if "UIO" in hw_name and UIO_Path != "":
                    firmware_file_name = UIO_Path
                elif "ELM" in hw_name and ELM_Path != "":
                    firmware_file_name = ELM_Path
                elif "MUX" in hw_name and IfMux_Path != "":
                    firmware_file_name = IfMux_Path
                elif "RDO" in hw_name and RDO_Path != "":
                    firmware_file_name = RDO_Path

            if firmware_file_name != None:
                #upload firmware.bin to the device
                print(f"Uploading {firmware_file_name} to {ip_addr}")
                res = upload_file(ip_addr, firmware_file_name, 'bootloader.bin')
                if res:
                    upload_file(ip_addr, Cmds_Path + find_cmd(cmd.INSTALL_BL), 'command.bin')
            else:
                print(f"File bootloader.bin not specifed for {app_name}")
        # for message in devices[device]:
        #     print(f"Message: {message}")
        #     for field in devices[device][message]:
        #         print(f"Field: {field} = {devices[device][message][field]}")


def vlan_header_get(vlan_id: int) -> bytes:
    if (0 < vlan_id < 4095):
        return b'\x81\x00' + vlan_id.to_bytes(2)
    return b''


def create_avtp_acf_can_frame(vlan_id: int = 0):
    # NOTE: handle_packet and other inner functions cannot handle VLAN tag in received packets yet
    # Ethernet header
    dst_mac = b'\xff\xff\xff\xff\xff\xff'  # Broadcast
    src_mac = b'\xe8\x6a\x64\xe7\x98\xf8'  # LCFCHeFe_e7:98:f8
    ethertype = b'\x22\xf0'  # IEEE 1722 Type
    # ethernet_header = dst_mac + src_mac + ethertype
    avtp_header = b'\x82\x80'
    # ACF-CAN Data
    # acf_can_frame = b'\x10\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x04\x0a\x00\x04\x00\xff\xfe\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    # Combine all parts
    # avtp_acf_can_frame = ethernet_header + avtp_header + acf_can_frame

    ntsc_stream_id = b'\x00\x00\x00\x00\x00\x00\x00\x01'
    acf_can_bus_id = b'\x00'
    acf_can_id = b'\x04\x00\xff\xfe'
    acf_can_data = b'\x1f\x00\x00\x00\x00\x00\x00\x00'
    acf_can_frame = b'\x10\x00' + ntsc_stream_id + b'\x04\x04\x0a' + acf_can_bus_id+ acf_can_id + acf_can_data
    # Combine all parts
    vlan_header = vlan_header_get(vlan_id)
    avtp_acf_can_frame = dst_mac + src_mac + vlan_header + ethertype + avtp_header + acf_can_frame

    trailer_len = 60 - len(avtp_acf_can_frame)
    if trailer_len > 0:
        trailer = bytes(trailer_len)
        avtp_acf_can_frame += trailer
    return avtp_acf_can_frame


def send_avtp_frame(frame, interface):
    # Create an Ethernet frame with Scapy
    # ethernet_frame = Ether(dst=BROADCAST_MAC) / frame
    # Send the frame
    sendp(frame, iface=interface, verbose=0)


def parse_acf_can_message(message, mac_addr_str):
    global devices
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

    data = message[8:(message_length_quadlets * 4 )]

    # Display the parsed data
    #print(f"CAN Brief: Type={message_type}, Is CANFD={flag_is_can_fd}, Length={frame_length}, Bus ID={bus_id}, CAN ID={can_id:08x}, Data={data.hex()}")
    #get the message with the can id
    #if message is MODULE_INFO_EX
    if can_id == 0x0c08fe01:
        #decode the message
        des_message = db.decode_message(0x0c08feFE, data)
        #create devices[mac_addr].MODULE_INFO_EX
        #chek if devices hax member mac_addr
        if mac_addr_str not in devices:
            devices[mac_addr_str] = {}
        devices[mac_addr_str]['MODULE_INFO_EX'] = des_message
        # devices[mac_addr].update({'MODULE_INFO_EX': {des_message}})
        # module_mac_addr = des_message['module_mac_addr']
        # module_chip_uid_1 = des_message['module_chip_uid_1']
        # module_chip_uid_2 = des_message['module_chip_uid_2']
        # module_ip_addr = des_message['module_ip_addr']

    #if message is MODULE_INFO
    if can_id == 0x0c01fe01:
        #decode the message
        des_message = db.decode_message(0x0c01feFE, data)
        # print(des_message)
        if mac_addr_str not in devices:
            devices[mac_addr_str] = {}
        devices[mac_addr_str]['MODULE_INFO'] = des_message

    #if message is PIN_INFO
    if can_id == 0x0c10fe01:
        des_message = db.decode_message(0x0c10fefe, data)

        if mac_addr_str not in devices:
            devices[mac_addr_str] = {}
        devices[mac_addr_str]['PIN_INFO'] = des_message


def parse_avtp_frame(frame):
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
            parse_acf_can_message(acf_can_message,src_mac_str)

            # Move to the next message
            offset += message_length_bytes


def handle_packet(packet):
    # Check if this is an AVTP packet
    if packet.haslayer(Ether):
        p = packet[Ether]
        if p.type == 0x22f0:
            # This is an AVTP packet, handle it here
            avtp_frame = bytes(p)
            parse_avtp_frame(avtp_frame)
    return


def sniff_packets(interface, stop_event):
    # Start sniffing the network
    # sniff(iface=interface, prn=handle_packet, stop_filter=stop_handler)
    sniffer = AsyncSniffer(iface=interface, prn=handle_packet, store=False)
    sniffer.start()
    try:
        stop_event.wait()
    finally:
        sniffer.stop()
        # print("Sniffing stopped")


def main():
    global UIO_Path
    global ELM_Path
    global IfMux_Path
    global RDO_Path
    global devices

    parser = argparse.ArgumentParser(description="Bootloader updater for SDRig")
    interface = "Ethernet"  # Replace with your network interface
    # Добавляем аргументы
    parser.add_argument("--iface", help="specify the network interface: example eth0 or enp0s3")
    parser.add_argument("--uio", help="specify the path to the firmware file of SODA.HIL.UIO module")
    parser.add_argument("--elm", help="specify the path to the firmware file of SODA.HIL.ELM module")
    parser.add_argument("--ifmux", help="specify the path to the firmware file of SODA.HIL.IFMUX module")
    parser.add_argument("--rdo", help="specify the path to the firmware file of SODA.SDR.RDO module")

    # Парсинг аргументов
    args = parser.parse_args()

    # Использование аргументов
    if args.iface:
        print("interface:", args.iface)
        interface = args.iface
    if args.uio:
        print("uio:", args.uio)
        UIO_Path = args.uio
    if args.elm:
        print("elm:", args.elm)
        ELM_Path = args.elm
    if args.ifmux:
        print("ifmux:", args.ifmux)
        IfMux_Path = args.ifmux
    if args.rdo:
        print("rdo:", args.rdo)
        RDO_Path = args.rdo

    # Start the receiver thread
    stop_sniffing = threading.Event()
    receiver_thread = threading.Thread(target=sniff_packets, args=(interface, stop_sniffing))
    receiver_thread.start()

    # Wait for the receiver to start
    #time.sleep(1)

    # Clear devices list
    devices = {}

    # Send an AVTP ACF-CAN frame
    avtp_frame = create_avtp_acf_can_frame()

    try:
        for _i in range(3):
            send_avtp_frame(avtp_frame, interface)
            time.sleep(0.05)

        time.sleep(1)

    finally:
        stop_sniffing.set()
        receiver_thread.join(timeout=5)

    print_devices()
    if receiver_thread.is_alive():
        print("Warning: thread did not terminate in time.")
    # else:
        # print("Thread terminated successfully.")
    return


if __name__ == "__main__":
    main()



