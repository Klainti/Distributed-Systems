"""A module for constructing and deconstructinga packet."""

import struct

MAX_NAME_LEGNTH = '150'
MAX_MSG_LEGTH = '870'

# Group IP, Group port, Name
JOIN_ENCODING = '!16si' + MAX_NAME_LEGNTH + 's'

# Name, Type (-1/ 1)
MEMBER_CONN_DIS_ENCODING = '!' + MAX_NAME_LEGNTH + 'si'

# Name, Message, Sequence number
MESSAGE_ENCODING = '!' + MAX_NAME_LEGNTH + 's' + MAX_MSG_LEGTH + 'si'

# Name
PREVIOUS_MEMBERS_ENCODING = '!' + MAX_NAME_LEGNTH + 's'


# Encode the packet for the already coonected members
def construct_prev_member_packet(name):
    return struct.pack(PREVIOUS_MEMBERS_ENCODING, name)


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
