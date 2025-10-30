from scapy.packet import Packet, bind_layers
from scapy.fields import BitField, ByteField, XByteField, ShortField, IntField, StrFixedLenField 
from scapy.layers.l2 import Ether


class AVTPPacket(Packet):
    name = "AVTPPacket"
    fields_desc = [
        #@TODO implement with BitField's
        #AVTP HEADER 1A Length
        XByteField("subtype", 0x82),    # AVTP Subtype: Non Time Synchronous Control Format (0x82) ieee1722.subtype
        ByteField("version_cd", 0x80),  # version and control/data indicator 
                                        # 1... .... = AVTP Stream ID Valid: True
                                        # .000 .... = AVTP Version: 0x0
        ByteField("data_length", 0x00), # Non-Time-Synchronous Control Format
                                        # .... 0... .... .... = Reserved bits: 0x0
                                        # .... .000 0000 0000 = Data Length: 0
        ByteField("sequence_number", 0),# media-reset, timestamp-valid
        IntField("stream_id_high", 0),  # High part of Stream ID
        IntField("stream_id_low", 1),   # Low part of Stream ID
        
        #ACF-CAN Message:

        ShortField("acf_header", 0x0404),#ACF Header: CAN Brief (0x02), 16 bytes with header
                                         #0000 010. .... .... = Message Type: CAN Brief (0x02)
                                         #.... ...0 0000 0100 = Message Length (Quadlets): 4

        ByteField("flags", 0x08),  #Flags: 0x08: pad=0, mtv=0, rtr=0, eff=1, brs=0, fdf=0, esi=0
                                    # 00.. .... = Padding Length: 0
                                    # ..0. .... = Message Timestamp Valid: False
                                    # .... ..0. = CAN Flexible Data-rate Format: False

        ByteField("can_id", 0x01),  #Bus Identifier: 1
                                    # 000. .... = Reserved Bits: 0x0
                                    # ...0 0001 = CAN Bus Identifier: 1

        IntField("msg_id", 0),      # CAN MSG ID
        StrFixedLenField("data", b'\x00'*64, length=64)  # CAN data up to 64 bytes for can-fd msg
    ]
    

    def extract_padding(self, s):
        return "", s  # No automatic padding extraction

    def stream_id(self):
        return (self.stream_id_high << 32) | self.stream_id_low

    def set_stream_id(self, stream_id: int):
        self.stream_id_high = (stream_id >> 32) & 0xFFFFFFFF
        self.stream_id_low = stream_id & 0xFFFFFFFF

AVTP_ETHERTYPE = 0x22F0
bind_layers(Ether, AVTPPacket, type=AVTP_ETHERTYPE)



if __name__ == "__main__":
    from scapy.all import sendp

    packet = Ether(dst="01:23:45:67:89:ab", type=0x22F0) / AVTPPacket()
    packet[AVTPPacket].subtype = 0x0A
    packet[AVTPPacket].set_stream_id(1)
    packet[AVTPPacket].data_length = 16
    packet[AVTPPacket].can_id = 1
    packet[AVTPPacket].msg_id = 0x100
    packet = packet / bytes([0x01, 0x02, 0x03, 0x04, 0xAA, 0xBB, 0xCC, 0xDD])  # payload

    packet.show()
    sendp(packet, iface="lo")
