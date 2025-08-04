import os
import socket
import struct
import time
import threading
from scapy.all import Ether, sendp, sniff
import cantools
import tftpy
import argparse

# Constants for Ethernet
ETH_P_ALL = 3
BROADCAST_MAC = 'ff:ff:ff:ff:ff:ff'
stop_sniffing = False
#cur dir
cur_dir = os.getcwd()
#load the dbc file
db = cantools.database.load_file('soda_xil_fd.dbc')
#init devices dictionary as list
devices = {}

global seq_num
global ethernet_header
global avtp_header
global stream_id

def print_devices():
    for device in devices:
        ip_addr = ""
        app_name = ""
        app_version = ""
        app_build_date = ""
        hw_name = ""
        bl_name = ""
        bl_version = ""
        bl_build_date = ""
        print("|-------------------------------------------------------------------|")
        #print(f"Device: {device}")
        if "MODULE_INFO" in devices[device]:
            if "module_app_fw_name_1" in devices[device]["MODULE_INFO"]:
                #convert devices[device]['MODULE_INFO']['module_app_fw_name_1'] to bytes
                devices[device]['MODULE_INFO']['module_app_fw_name_1'] = devices[device]['MODULE_INFO']['module_app_fw_name_1'].to_bytes(8, 'little') 
                #decode the bytes to string
                devices[device]['MODULE_INFO']['module_app_fw_name_1'] = devices[device]['MODULE_INFO']['module_app_fw_name_1'].decode('utf-8')
                #print(f"Device Name: {devices[device]['MODULE_INFO']['module_app_fw_name_1']}")
                
                if "module_app_fw_name_2" in devices[device]["MODULE_INFO"]:
                    #convert devices[device]['MODULE_INFO']['module_app_fw_name_2'] to bytes
                    devices[device]['MODULE_INFO']['module_app_fw_name_2'] = devices[device]['MODULE_INFO']['module_app_fw_name_2'].to_bytes(8, 'little') 
                    #decode the bytes to string
                    devices[device]['MODULE_INFO']['module_app_fw_name_2'] = devices[device]['MODULE_INFO']['module_app_fw_name_2'].decode('utf-8')
                    devices[device]['MODULE_INFO']['module_app_fw_name_1'] = devices[device]['MODULE_INFO']['module_app_fw_name_1'] + devices[device]['MODULE_INFO']['module_app_fw_name_2']
                    # print(f"Device Name: {devices[device]['MODULE_INFO']['module_app_fw_name_1']}")
                    if "module_app_fw_name_3" in devices[device]["MODULE_INFO"]:
                        #convert devices[device]['MODULE_INFO']['module_app_fw_name_3'] to bytes
                        devices[device]['MODULE_INFO']['module_app_fw_name_3'] = devices[device]['MODULE_INFO']['module_app_fw_name_3'].to_bytes(8, 'little') 
                        #decode the bytes to string
                        devices[device]['MODULE_INFO']['module_app_fw_name_3'] = devices[device]['MODULE_INFO']['module_app_fw_name_3'].decode('utf-8')
                        devices[device]['MODULE_INFO']['module_app_fw_name_1'] = devices[device]['MODULE_INFO']['module_app_fw_name_1'] + devices[device]['MODULE_INFO']['module_app_fw_name_3']
                        # print(f"App Name: {devices[device]['MODULE_INFO']['module_app_fw_name_1']}")
                        #get string value of devices[device]['MODULE_INFO']['module_app_fw_name_1']
                        
                app_name = devices[device]['MODULE_INFO']['module_app_fw_name_1'].rstrip("\x00")

                app_version = f"{devices[device]['MODULE_INFO']['module_app_ver_gen']}." \
                                f"{devices[device]['MODULE_INFO']['module_app_ver_major']}." \
                                f"{devices[device]['MODULE_INFO']['module_app_ver_minor']}." \
                                f"{devices[device]['MODULE_INFO']['module_app_ver_fix']}." \
                                f"{devices[device]['MODULE_INFO']['module_app_ver_build']}"
                app_version = f"{app_version} {devices[device]['MODULE_INFO']['module_app_target']}"

                app_build_date = f"{devices[device]['MODULE_INFO']['module_app_build_hour']:02d}:" \
                                    f"{devices[device]['MODULE_INFO']['module_app_build_min']:02d} " \
                                    f"{devices[device]['MODULE_INFO']['module_app_build_day']:02d}/" \
                                    f"{devices[device]['MODULE_INFO']['module_app_build_month']:02d}/" \
                                    f"{devices[device]['MODULE_INFO']['module_app_build_year']:04d}"

            if "module_app_hw_name_1" in devices[device]["MODULE_INFO"]:
                #convert devices[device]['MODULE_INFO']['module_app_hw_name_1'] to bytes
                devices[device]['MODULE_INFO']['module_app_hw_name_1'] = devices[device]['MODULE_INFO']['module_app_hw_name_1'].to_bytes(8, 'little') 
                #decode the bytes to string
                devices[device]['MODULE_INFO']['module_app_hw_name_1'] = devices[device]['MODULE_INFO']['module_app_hw_name_1'].decode('utf-8')
                #print(f"Device Name: {devices[device]['MODULE_INFO']['module_app_hw_name_1']}")
                if "module_app_hw_name_2" in devices[device]["MODULE_INFO"]:
                    #convert devices[device]['MODULE_INFO']['module_app_hw_name_2'] to bytes
                    devices[device]['MODULE_INFO']['module_app_hw_name_2'] = devices[device]['MODULE_INFO']['module_app_hw_name_2'].to_bytes(8, 'little') 
                    #decode the bytes to string
                    devices[device]['MODULE_INFO']['module_app_hw_name_2'] = devices[device]['MODULE_INFO']['module_app_hw_name_2'].decode('utf-8')
                    devices[device]['MODULE_INFO']['module_app_hw_name_1'] = devices[device]['MODULE_INFO']['module_app_hw_name_1'] + devices[device]['MODULE_INFO']['module_app_hw_name_2']
                # print(f"Hw Name: {devices[device]['MODULE_INFO']['module_app_hw_name_1']}")
                hw_name = devices[device]['MODULE_INFO']['module_app_hw_name_1']
        if "MODULE_INFO_EX" in devices[device]:
            if "module_ip_addr" in devices[device]["MODULE_INFO_EX"]:
                #convert devices[device]['MODULE_INFO_EX']['module_ip_addr'] to bytes
                devices[device]['MODULE_INFO_EX']['module_ip_addr'] = devices[device]['MODULE_INFO_EX']['module_ip_addr'].to_bytes(4, 'big') 
                #decode the bytes to string
                devices[device]['MODULE_INFO_EX']['module_ip_addr'] = socket.inet_ntoa(devices[device]['MODULE_INFO_EX']['module_ip_addr'])
                # print(f"IP Address: {devices[device]['MODULE_INFO_EX']['module_ip_addr']}")
                ip_addr = devices[device]['MODULE_INFO_EX']['module_ip_addr']
        
        if "MODULE_INFO_BOOT" in devices[device]:
            if "module_app_fw_name_1" in devices[device]["MODULE_INFO_BOOT"]:
                #convert devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] to bytes
                devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'].to_bytes(8, 'little') 
                #decode the bytes to string
                devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'].decode('utf-8')
                #print(f"Device Name: {devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1']}")
                
                if "module_app_fw_name_2" in devices[device]["MODULE_INFO_BOOT"]:
                    #convert devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2'] to bytes
                    devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2'].to_bytes(8, 'little') 
                    #decode the bytes to string
                    devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2'].decode('utf-8')
                    devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] + devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_2']
                    # print(f"Device Name: {devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1']}")
                    if "module_app_fw_name_3" in devices[device]["MODULE_INFO_BOOT"]:
                        #convert devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3'] to bytes
                        devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3'].to_bytes(8, 'little') 
                        #decode the bytes to string
                        devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3'].decode('utf-8')
                        devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'] + devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_3']
                        # print(f"App Name: {devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1']}")
                        #get string value of devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1']
                        
                bl_name = devices[device]['MODULE_INFO_BOOT']['module_app_fw_name_1'].rstrip("\x00")

                bl_version = f"{devices[device]['MODULE_INFO_BOOT']['module_app_ver_gen']}." \
                                f"{devices[device]['MODULE_INFO_BOOT']['module_app_ver_major']}." \
                                f"{devices[device]['MODULE_INFO_BOOT']['module_app_ver_minor']}." \
                                f"{devices[device]['MODULE_INFO_BOOT']['module_app_ver_fix']}." \
                                f"{devices[device]['MODULE_INFO_BOOT']['module_app_ver_build']}"
                bl_version = f"{bl_version} {devices[device]['MODULE_INFO_BOOT']['module_app_target']}"

                bl_build_date = f"{devices[device]['MODULE_INFO_BOOT']['module_app_build_hour']:02d}:" \
                                    f"{devices[device]['MODULE_INFO_BOOT']['module_app_build_min']:02d} " \
                                    f"{devices[device]['MODULE_INFO_BOOT']['module_app_build_day']:02d}/" \
                                    f"{devices[device]['MODULE_INFO_BOOT']['module_app_build_month']:02d}/" \
                                    f"{devices[device]['MODULE_INFO_BOOT']['module_app_build_year']:04d}"

        if ip_addr != "" and app_name != "" and hw_name != "":
            print(f"Device Name: {hw_name} {app_name}")
            print(f"Device Version: {app_version} {app_build_date}")
            print(f"IP Address: {ip_addr}")
            if bl_name != "" and bl_version != "" and bl_build_date != "":
                print(f"Device BL Name: {bl_name} {bl_version} {bl_build_date}")

        # for message in devices[device]:
        #     print(f"Message: {message}")
        #     for field in devices[device][message]:
        #         print(f"Field: {field} = {devices[device][message][field]}")


def avtp_init():
    global seq_num
    global ethernet_header
    global avtp_header
    global stream_id

    seq_num = 0
    # Ethernet header
    dst_mac = b'\xff\xff\xff\xff\xff\xff'  # Broadcast
    src_mac = b'\xe8\x6a\x64\xe7\x98\xf8'  # LCFCHeFe_e7:98:f8
    ethertype = b'\x22\xf0'  # IEEE 1722 Type
    ethernet_header = dst_mac + src_mac + ethertype
    avtp_header = b'\x82\x80'
    stream_id = b'\x00\x00\x00\x00\x00\x00\x00\x01'


def avtp_seq_num_inc():
    global seq_num
    seq_num += 1
    if (seq_num > 0xff):
        seq_num = 0


def avtp_calc_acf_frame_len(frame: bytes, add_len: int) -> bytes:
    frame_list = list(frame)
    acf_frame_len = ((frame_list[15] & 0x07) << 8) + frame_list[16]
    acf_frame_len += add_len
    frame_list[15] = (frame_list[15] & 0xf8) | (acf_frame_len >> 8)
    frame_list[16] = acf_frame_len & 0xff
    new_frame = bytes(frame_list)
    return new_frame


def create_avtp_acf_can_frame():
    global ethernet_header
    global avtp_header
    acf_can_frame = b'\x10\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x04\x0a\x00\x04\x00\xff\xfe\x3f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    # Combine all parts
    avtp_acf_can_frame = ethernet_header + avtp_header + acf_can_frame
    return avtp_acf_can_frame


def create_avtp_acf_can_msg(can_id: bytes, data: bytes):
    acf_can_msg_len = 8 + len(data)
    quadlets = int(acf_can_msg_len/4)
    acf_can_msg = b'\x04' + quadlets.to_bytes(1, 'big') + b'\x0a\x00' + can_id + data
    # print(f'ACF can msg: {acf_can_msg}')
    return acf_can_msg


def avtp_acf_can_frame_create() -> bytes:
    global seq_num
    global ethernet_header
    global avtp_header
    global stream_id
    avtp_acf_can_frame = ethernet_header + avtp_header + b'\x00' + seq_num.to_bytes(1, 'big')  + stream_id  # length is now 0
    # print(f'ACF can frame: {avtp_acf_can_frame}')
    avtp_seq_num_inc()
    return avtp_acf_can_frame


def avtp_acf_can_frame_add(frame: bytes, acf_can_msg: bytes) -> bytes:
    # change total length
    frame = avtp_calc_acf_frame_len(frame, len(acf_can_msg))
    frame += acf_can_msg
    return frame

def avtp_acf_can_frame_finalize(frame: bytes) -> bytes:
    frame_len = len(frame)
    if frame_len < 60:
        frame += b'\x00' * (60 - frame_len)
    # print(f'ACF can final frame: {frame}')
    return frame

def send_avtp_frame(frame, interface):
    # Create an Ethernet frame with Scapy
    ethernet_frame = Ether(dst=BROADCAST_MAC) / frame
    # Send the frame
    sendp(frame, iface=interface, verbose=0)


def stop_receiver():
    # Set the global stop_sniffing variable to True
    global stop_sniffing
    stop_sniffing = True


def stop_handler(frame):
    global stop_sniffing
    return stop_sniffing


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
    
    #if message is MODULE_INFO_BOOT
    if can_id == 0x0c02fe01:
        #decode the message
        des_message = db.decode_message(0x0c02feFE, data)
        # print(des_message)
        if mac_addr_str not in devices:
            devices[mac_addr_str] = {}
        devices[mac_addr_str]['MODULE_INFO_BOOT'] = des_message

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
    if packet.haslayer(Ether) and packet[Ether].type == 0x22f0:
        # This is an AVTP packet, handle it here
        avtp_frame = bytes(packet[Ether])
        parse_avtp_frame(avtp_frame)

    # return stop_sniffing # Note: causes printing of these results after an invocation of the function in sendrecv.py/_run


def receive_avtp_frames(interface):
    # Start sniffing the network
    sniff(iface=interface, prn=handle_packet, stop_filter=stop_handler)


def main():
    parser = argparse.ArgumentParser(description="LAN load simulation")
    interface = "Ethernet"  # Replace with your network interface
    # Добавляем аргументы
    parser.add_argument("--iface", help="specify the network interface: example eth0 or enp0s3")
    parser.add_argument("--time", help="specify the time length of loading the LAN, seconds")
    parser.add_argument("--int", help="specify the time interval between sendings, seconds")

    # Парсинг аргументов
    args = parser.parse_args()

    # Использование аргументов
    if args.iface:
        print("interface:", args.iface)
        interface = args.iface
    if args.time:
        print("time:", args.time)
        seconds = int(args.time)
    if args.int:
        print("interval:", args.int)
        interval = float(args.int)

    # Start the receiver thread
    receiver_thread = threading.Thread(target=receive_avtp_frames, args=(interface,))
    receiver_thread.start()

    # Wait for the receiver to start
    #time.sleep(1)

    avtp_init()

    # Send an AVTP ACF-CAN frame
    # frame = create_avtp_acf_can_frame()

    try:
        # FIRST VARIANT: together
        frame = avtp_acf_can_frame_create()
        frame = avtp_acf_can_frame_add(frame, create_avtp_acf_can_msg(bytes.fromhex("0c00fffe"), bytes.fromhex("0000000000000000")))
        frame = avtp_acf_can_frame_add(frame, create_avtp_acf_can_msg(bytes.fromhex("0c21fffe"), bytes.fromhex("22") * 8))
        frame = avtp_acf_can_frame_add(frame, create_avtp_acf_can_msg(bytes.fromhex("0d21fffe"), bytes.fromhex("00") * 20))
        # 86 bytes

        frame = avtp_acf_can_frame_finalize(frame)

        t_end = time.time() + seconds
        while time.time() < t_end:
            send_avtp_frame(frame, interface)
            # time.sleep(interval)


        # # SECOND VARIANT: Not together
        # frame1 = avtp_acf_can_frame_create()
        # frame1 = avtp_acf_can_frame_add(frame1, create_avtp_acf_can_msg(bytes.fromhex("0c00fffe"), bytes.fromhex("0000000000000000")))

        # frame2 = avtp_acf_can_frame_create()
        # frame2 = avtp_acf_can_frame_add(frame2, create_avtp_acf_can_msg(bytes.fromhex("0c21fffe"), bytes.fromhex("22") * 8))

        # frame3 = avtp_acf_can_frame_create()
        # frame3 = avtp_acf_can_frame_add(frame3, create_avtp_acf_can_msg(bytes.fromhex("0d21fffe"), bytes.fromhex("00") * 20))

        # frame1 = avtp_acf_can_frame_finalize(frame1)
        # frame2 = avtp_acf_can_frame_finalize(frame2)
        # frame3 = avtp_acf_can_frame_finalize(frame3)

        # t_end = time.time() + seconds
        # while time.time() < t_end:
        #     send_avtp_frame(frame1, interface)
        #     send_avtp_frame(frame2, interface)
        #     send_avtp_frame(frame3, interface)
        #     # time.sleep(interval)

    finally:
        stop_receiver()
        receiver_thread.join(timeout=5)

    # time.sleep(1)
    # print_devices()


if __name__ == "__main__":
    main()



