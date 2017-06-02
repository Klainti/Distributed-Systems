"""A module for constructing and deconstructing a packet."""

import struct


# Custom ERROR
class LengthError(Exception):
    def __init__(self, message):
        self.message = message


# CONSTANTS
BLOCK_SIZE = 16380

NAME_LENGTH = 150

OPEN_REQ = 1
READ_REQ = 2
WRITE_REQ = 3

# ENCODINGS

# Type, request number, create/open, File name
OPEN_ENCODING = '!iii' + str(NAME_LENGTH) + 's'

# Type, request number, Fd, starting pos, size_of_data, data
WRITE_ENCODING = '!iiiii' + str(BLOCK_SIZE) + 's'
WRITE_REQ_SIZE = 5*4 + BLOCK_SIZE

# Type, request number, Fd, pos, length
READ_REQ_ENCODING = '!iiiii'

# Request number, number_of_packet, total_packets, size_of_data, data
READ_REP_ENCODING = '!iiii' + str(BLOCK_SIZE) + 's'
READ_REP_SIZE = 4*4 + BLOCK_SIZE

# CLIENT FUNCTIONS

# Encode the packet for the create request
def construct_open_packet(request_number, create, name):
    if (len(name) > NAME_LENGTH):
        raise LengthError, "Too big name"
    return struct.pack(OPEN_ENCODING, OPEN_REQ,request_number, create, name)


# Encode the packet for the write request
def construct_write_packet(request_number, fd, pos, data):
    if (len(data) > BLOCK_SIZE):
        raise LengthError, "Too many data"
    return struct.pack(WRITE_ENCODING, WRITE_REQ, request_number, fd, pos, len(data), data)


# Encode the packet for the read request
def construct_read_packet(request_number, fd, pos, length):
    if (length <= 0):
        raise LengthError, "Unacceptable Length"
    return struct.pack(READ_REQ_ENCODING, READ_REQ, request_number, fd, pos, length)


# SERVER FUNCTIONS

# Encode the packet for the read request
def construct_read_rep_packet(request_number, cur_num, total, data):
    return struct.pack(READ_REP_ENCODING, request_number, cur_num, total, len(data), data)


# COMMON FUNCTION

# Deconstruct a packet
def deconstruct_packet(decode, packet):
    return struct.unpack(decode, packet)
