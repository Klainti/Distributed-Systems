"""A module for constructing and deconstructinga packet."""

import struct

JOIN_ENCODING = '!16si50s'
MEMBER_CONN_DIS_ENCODING = '!50si'


# Encode the packet to announce new member
def construct_member_packet(name, Type):
    return struct.pack(MEMBER_CONN_DIS_ENCODING, name, Type)


# Encode the packet for a new member details!
def construct_join_packet(ip, port, name):
    return struct.pack(JOIN_ENCODING, ip, port, name)


# Deconstruct a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
