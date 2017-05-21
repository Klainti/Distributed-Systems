"""network file system API."""

import socket
import struct
import threading
import packet_struct

# Global variables!
SERVER_ADDR = ()
udp_socket = None

#counter for requests!
seq_num = 0

"""Initialize connection with server"""
def init_connection():

    global udp_socket

    # create socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # start nfs threads!

"""Set SERVER INFO"""
def mynfs_setSrv(ipaddr, port):

    global SERVER_ADDR

    # stores info for server
    SERVER_ADDR = (ipaddr, port)

    init_connection()
    return 1

"""Send Open request"""
def mynfs_open(fname, create, cacheFreshnessT):

    global udp_socket, seq_num

    seq_num += 1

    # create and send the open request!
    packet_req = packet_struct.construct_open_packet(seq_num, create, fname)
    udp_socket.sendto(packet_req, SERVER_ADDR)

    # wait for reply (JUST THE FD!)
    return struct.unpack('!i', udp_socket.recv(4))[0]
