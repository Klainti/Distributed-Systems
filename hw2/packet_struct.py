''' A module for constructing and deconstructing
    a packet'''

BROADCAST_ENCODING='!16sii'

REQ_ENCODING = '!1020si'

import struct

def construct_broadcast_packet(encode,ip,port,svcid):
    return struct.pack(encode,ip,port,svcid)

def construct_packet(encode, data, reqid):
    return struct.pack(encode,data, reqid)

def deconstruct_packet(decode,packet):
    return struct.unpack(decode,packet)
