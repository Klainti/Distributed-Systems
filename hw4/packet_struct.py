"""A module for constructing and deconstructing a packet."""

import struct


# Custom ERROR
class LengthError(Exception):
    def __init__(self, message):
        self.message = message


# CONSTANTS
BLOCK_SIZE = 989

NAME_LENGTH = 150

OPEN_REQ = 1
READ_REQ = 2
WRITE_REQ = 3

# ENCODINGS

# Type, req_number, create/open, File name
OPEN_ENCODING = '!iii' + str(NAME_LENGTH) + 's'

# Type, req_number, Fd, starting pos, current_number_of_packet, total_packets, size_of_data, data
WRITE_ENCODING = '!iiiiiii' + str(BLOCK_SIZE) + 's'

# Type, req_number, Fd, pos, length
READ_REQ_ENCODING = '!iiiii'


# req_number, number_of_packet, total_packets, size_of_data, data
READ_REP_ENCODING = '!iiii' + str(BLOCK_SIZE) + 's'


# ACK for request with Req_number
ACK_ENCODING = '!i'


# CLIENT FUNCTIONS

# Encode the packet for the create request
def construct_open_packet(req_number, create, name):
    if (len(name) > NAME_LENGTH):
        raise LengthError, "Too big name"
    return struct.pack(OPEN_ENCODING, OPEN_REQ, req_number, create, name)


# Encode the packet for the write request
def construct_write_packet(req_number, fd, pos, cur_num, total, data):
    if (len(data) > BLOCK_SIZE):
        raise LengthError, "Too many data"
    return struct.pack(WRITE_ENCODING, WRITE_REQ, req_number, fd, pos, cur_num, total, len(data), data)


# Encode the packet for the read request
def construct_read_packet(req_number, fd, pos, length):
    if (length <= 0):
        raise LengthError, "Unacceptable Length"
    return struct.pack(READ_REQ_ENCODING, READ_REQ, req_number, fd, pos, length)


# SERVER FUNCTIONS

# Encode the packet for the read request
def construct_read_rep_packet(req_number, cur_num, total, data):
    return struct.pack(READ_REP_ENCODING, req_number, cur_num, total, len(data), data)


# Encode the packet for the read request
def construct_ACK(req_number):
    return struct.pack(ACK_ENCODING, req_number)


# COMMON FUNCTION

# Deconstruct a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
