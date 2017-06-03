"""Service support network file system."""

import sys
sys.path.append('../../hw4')

import socket
import struct
import os
import threading

import packet_struct

# Global Variables
udp_socket = None

# counter of file descriptors!
c_fd = 0

# {key = a number: value= file descriptor}
fd_dict = {}

write_requests_lock = threading.Lock()
write_requests = {}

read_requests_lock = threading.Lock()
# Client info, request number, fd, pos, length
read_requests = []

open_requests_lock = threading.Lock()
# Client info, request number, file name, create/open
open_requests = []

"""Initialize service"""
def init_srv():

    global udp_socket
    udp_port = 0

    s1 = os.popen('/sbin/ifconfig wlan0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    s2 = os.popen('/sbin/ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    if (len(s1) > 16 or len(s1) < 7):
        MY_IP = s2.strip('\n')
    else:
        MY_IP = s1.strip('\n')

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((MY_IP, udp_port))
    udp_port = udp_socket.getsockname()[1]

    print 'Service location: ({},{})'.format(MY_IP, udp_port)

"""Serves an open request"""
def serve_open_request(packet, client_info):

    global c_fd, fd_dict, udp_socket

    #unpack packet
    req_number, create_open, filename = packet_struct.deconstruct_packet(packet_struct.OPEN_ENCODING, packet)[1:]

    filename = filename.strip('\0')

    # check first if valid req_number or it is dupli - Takis
    # else not valid - function fails - send to client -1

    if (create_open == 0):
        # create a file
        tmp_fd = open(filename, 'w+')
    else:
        # open a file that already exists!
        tmp_fd = open(filename, 'r+')

    # update fd_dict
    c_fd += 1
    fd_dict[c_fd] = tmp_fd

    # notify client with file descriptor
    udp_socket.sendto(struct.pack('!ii', req_number, c_fd), client_info)

"""Serves a read request"""
def serve_read_request(packet, client_info):

    global udp_socket
    # unpack packet
    req_number, fd, pos, length = packet_struct.deconstruct_packet(packet_struct.READ_REQ_ENCODING, packet)[1:]

    data = []

    local_fd = fd_dict[fd]

    # seek relative to the current position
    local_fd.seek(pos, 0)

    # get total reads!
    total_reads = int(length/packet_struct.BLOCK_SIZE)
    if (length % packet_struct.BLOCK_SIZE != 0):
        total_reads += 1

    for i in xrange(0, total_reads):
        buf = local_fd.read(packet_struct.BLOCK_SIZE)
        data.append(buf)
        if (len(buf) == 0):
            break



    total_reads = len(data)

    for i in xrange(total_reads):

        # print "Send data", i+1, "/", total_reads, len(data[i])

        reply_packet =packet_struct.construct_read_rep_packet(req_number, i, total_reads, data[i])

        #if (i%2 == 0):
        udp_socket.sendto(reply_packet, client_info)

"""Serves a write request"""
def serve_write_request(packet, client_info):

    global udp_socket

    # print 'packet len: {}'.format(len(packet))
    req_number, fd, pos, size_of_data, data = packet_struct.deconstruct_packet(packet_struct.WRITE_ENCODING, packet)[1:]
    data = data.strip('\0')

    local_fd = fd_dict[fd]

    # seek relative to the current position
    local_fd.seek(pos, 0)

    # print "Write at", pos, size_of_data

    local_fd.write(data)
    local_fd.flush()

    reply_packet = struct.pack('!i', req_number)

    udp_socket.sendto(reply_packet, client_info)

"""Receive requests from clients!"""
def receive_from_clients():

    global udp_socket

    while(1):
        packet, client_info = udp_socket.recvfrom(packet_struct.WRITE_REQ_SIZE)

        # Get only the type of the request!
        type_of_req = struct.unpack_from('!i', packet[:4])[0]

        if (type_of_req == packet_struct.OPEN_REQ):
            # print "Got open request"

            req_number, create_open, filename = packet_struct.deconstruct_packet(packet_struct.OPEN_ENCODING, packet)[1:]

            serve_open_request(packet, client_info)

        elif (type_of_req == packet_struct.READ_REQ):
            # print "Got read request"

            req_number, fd, pos, length = packet_struct.deconstruct_packet(packet_struct.READ_REQ_ENCODING, packet)[1:]

            serve_read_request(packet, client_info)

        elif (type_of_req == packet_struct.WRITE_REQ):
            # print "Got write request"

            req_number, fd, pos, size_of_data, data = packet_struct.deconstruct_packet(packet_struct.WRITE_ENCODING, packet)[1:]
            data = data.strip('\0')

            serve_write_request(packet, client_info)
        else:
            pass

if __name__ == "__main__":
    init_srv()
    while(True):
        receive_from_clients()
