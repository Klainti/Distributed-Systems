"""Service support network file system."""

import sys
sys.path.append('../../hw4')

import socket
import struct
import os
import packet_struct

# Global Variables
udp_socket = None

# counter of file descriptors!
c_fd = 0

# {key = a number: value= file descriptor}
fd_dict = {}

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
    req_number, create_open, filename = packet_struct.deconstruct_packet(packet_struct.OPEN_ENCODING, packet)

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
    udp_socket.sendto(struct.pack('!i', c_fd), client_info)
    return 1

"""Serves a read request"""
def serve_read_request(packet, client_info):

    global udp_socket
    # unpack packet
    req_number, fd, pos, length = packet_struct.deconstruct_packet(packet_struct.READ_REQ_ENCODING, packet)

    local_fd = fd_dict[fd]

    # seek relative to the current position
    local_fd.seek(pos, 0)

    # get total reads!
    total_reads = int(length/1024)
    if (length % 1024 != 0):
        total_reads += 1

    for i in xrange(0, total_reads):
        data = local_fd.read(length)

        reply_packet = struct.pack('!1024s', data)

        udp_socket.sendto(reply_packet, client_info)

    return 1

"""Serves a write request"""
def serve_write_request(packet, client_info):

    global udp_socket

    print 'packet len: {}'.format(len(packet))
    req_number, fd, pos, current_number_of_packet, total_packets, size_of_data, data = packet_struct.deconstruct_packet(packet_struct.WRITE_ENCODING, packet)
    data = data.strip('\0')

    local_fd = fd_dict[fd]

    # seek relative to the current position
    local_fd.seek(pos, 0)

    local_fd.write(data)
    local_fd.flush()

    reply_packet = struct.pack('!i', req_number)

    udp_socket.sendto(reply_packet, client_info)

    return 1

"""Receive requests from clients!"""
def receive_from_clients():

    global udp_socket

    while(1):
        packet, client_info = udp_socket.recvfrom(1024)

        # Get only the type of the request!
        type_of_req = struct.unpack_from('!i', packet[:4])[0]

        if (type_of_req == packet_struct.OPEN_REQ):
            print "Got open request"
            serve_open_request(packet, client_info)
        elif (type_of_req == packet_struct.READ_REQ):
            print "Got read request"
            serve_read_request(packet, client_info)
        elif (type_of_req == packet_struct.WRITE_REQ):
            print "Got write request"
            serve_write_request(packet, client_info)
        else:
            pass

if __name__ == "__main__":
    init_srv()
    while(True):
        receive_from_clients()
