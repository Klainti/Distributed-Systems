"""A module for constructing and deconstructinga packet."""

import struct

# Group IP, Group port, Name
JOIN_ENCODING = '!16si50s'

# Name, Type (-1/ 1)
MEMBER_CONN_DIS_ENCODING = '!50si'

# Name, Message, Sequence number
MESSAGE_ENCODING = '!150s870si'


# Encode the packet to announce new member
def construct_member_packet(name, Type):
    return struct.pack(MEMBER_CONN_DIS_ENCODING, name, Type)


# Encode the packet for a new member details!
def construct_join_packet(ip, port, name):
    return struct.pack(JOIN_ENCODING, ip, port, name)

# Encode the packet for a new member details!
def construct_message_packet(name, message, seq_num):
    return struct.pack(MESSAGE_ENCODING, name, message, seq_num)

# Deconstruct a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
