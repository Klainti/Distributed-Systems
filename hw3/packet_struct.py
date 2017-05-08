"""A module for constructing and deconstructinga packet."""

import struct

MAX_NAME_LEGNTH = '150'
MAX_MSG_LEGTH = '870'

# Group IP, Group port, Name
JOIN_ENCODING = '!16si' + MAX_NAME_LEGNTH + 's'

# Group IP, Group port, Name, last_received_seq_number
LEAVE_ENCODING = '!16si' + MAX_NAME_LEGNTH + 'si'

# Name, Type (-1/ 1), last_acked_seq_number(only at disconnected)
MEMBER_CONN_DIS_ENCODING = '!' + MAX_NAME_LEGNTH + 'sii'

# Name, Message, Sequence number
MESSAGE_ENCODING = '!' + MAX_NAME_LEGNTH + 's' + MAX_MSG_LEGTH + 'si'

# Name
PREVIOUS_MEMBERS_ENCODING = '!' + MAX_NAME_LEGNTH + 's'

# Name, seq_num
VALID_MESSAGE = '!' + MAX_NAME_LEGNTH + 'si'


# Encode the packet for the already coonected members
def construct_prev_member_packet(name):
    return struct.pack(PREVIOUS_MEMBERS_ENCODING, name)


# Encode the packet to announce for connection or disconnection
def construct_member_packet(name, Type, last_acked_seq_num):
    return struct.pack(MEMBER_CONN_DIS_ENCODING, name, Type, last_acked_seq_num)


# Encode the packet for a new member details!
def construct_join_packet(ip, port, name):
    return struct.pack(JOIN_ENCODING, ip, port, name)


# Encode the packet for a new member details!
def construct_leave_packet(ip, port, name, last_seq_number):
    return struct.pack(LEAVE_ENCODING, ip, port, name, last_seq_number)


# Encode the packet for a new member details!
def construct_message_packet(name, message, seq_num):
    return struct.pack(MESSAGE_ENCODING, name, message, seq_num)


# Encode the packet for the valid message
def construct_valid_message_packet(name, seq_num):
    return struct.pack(VALID_MESSAGE, name, seq_num)


# Deconstruct a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
