"""network file system API."""

import socket
import struct
import threading
import packet_struct

# Global variables!
SERVER_ADDR = ()
udp_socket = None



variables_lock = threading.Lock()
fd_pos = {}

# counter for requests!
req_num = 0


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

    global udp_socket, req_num

    variables_lock.acquire()
    req_num += 1
    cur_req_num = req_num
    variables_lock.release()

    # create and send the open request!
    packet_req = packet_struct.construct_open_packet(cur_req_num, create, fname)
    udp_socket.sendto(packet_req, SERVER_ADDR)

    # wait for reply (JUST THE FD!)
    fd = struct.unpack('!i', udp_socket.recv(4))[0]

    variables_lock.acquire()
    fd_pos[fd] = 0
    variables_lock.release()

    return fd


"""Read n bytes from fd starting from position fd_pos[fd]"""
def mynfs_read(fd, n):

    global req_num

    variables_lock.acquire()
    pos = fd_pos[fd]
    req_num += 1
    cur_req_num = req_num
    variables_lock.release()

    packet = packet_struct.construct_read_packet(cur_req_num, fd, pos, n)
    udp_socket.sendto(packet, SERVER_ADDR)

    # Wait here for reply
    # Update fd_pos
    # Return data


"""Change pointer's position in fd"""
def mynfs_seek(fd, pos):

    variables_lock.acquire()
    fd_pos[fd] = pos
    variables_lock.release()
