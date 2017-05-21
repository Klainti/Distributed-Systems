"""network file system API."""

import socket
import struct
import threading
import packet_struct

# Global variables!
SERVER_ADDR = ()
udp_socket = None

# counter for requests!
seq_num_lock = threading.Lock()
seq_num = 0

buffers_lock = threading.Lock()
fd_pos = {}


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

    seq_num_lock.acquire()
    seq_num += 1
    cur_seq_num = seq_num
    seq_num_lock.release()

    # create and send the open request!
    packet_req = packet_struct.construct_open_packet(cur_seq_num, create, fname)
    udp_socket.sendto(packet_req, SERVER_ADDR)

    # wait for reply (JUST THE FD!)
    fd = struct.unpack('!i', udp_socket.recv(4))[0]

    buffers_lock.acquire()
    fd_pos[fd] = 0
    buffers_lock.release()

    return fd


"""Change pointer's position in fd"""
def mynfs_seek(fd, pos):

    buffers_lock.acquire()
    fd_pos[fd] = pos
    buffers_lock.release()
