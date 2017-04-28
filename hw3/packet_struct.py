''' A module for constructing and deconstructing
    a packet'''

JOIN_ENCODING = '!16si50s'
MEMBER_CONN_DIS_ENCODING = '!50si'

import struct

def construct_member_packet(name, Type):
    return struct.pack(JOIN_ENCODING, name, Type)

def construct_join_packet(ip, port, name):
    return struct.pack(JOIN_ENCODING, ip, port, name)

def deconstruct_packet(decode,packet):
    return struct.unpack(decode,packet)
