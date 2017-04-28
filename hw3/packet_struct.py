"""A module for constructing and deconstructinga packet."""

import struct

JOIN_ENCODING = '!16si50s'
MEMBER_CONN_DIS_ENCODING = '!50si'


# Encode the packet for join to service!
def construct_member_packet(name, Type):
    return struct.pack(JOIN_ENCODING, name, Type)


# Encode the packet for the group details!
def construct_join_packet(ip, port, name):
    return struct.pack(JOIN_ENCODING, ip, port, name)


# Deconstrung a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
