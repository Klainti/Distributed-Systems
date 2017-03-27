''' A module for constructing and deconstructing
    a packet'''

import struct

def construct_packet(encode,ip,port,svcid):
    return struct.pack(encode,ip,port,svcid)

def deconstruct_packet(decode,packet):
    return struct.unpack(decode,packet)
