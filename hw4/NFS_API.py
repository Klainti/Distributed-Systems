"""network file system API."""

import socket
import struct
import time
import threading
import packet_struct

# Global variables!
SERVER_ADDR = ()
udp_socket = None

# INIT VALUE OF TIMEOUT (ms)
TIMEOUT = 0.003
sum_time = 0
times = 0



variables_lock = threading.Lock()
fd_pos = {}

# counter for requests!
req_num = 0

"""Update timeout of the udp socket"""
def update_timeout(new_time):

    global udp_socket, sum_time, times

    sum_time += new_time
    times += 1
    if (times >= 10):
        avg_time = round(float(sum_time/times), 4)
        print "AVG TIME: {}".format(avg_time)
        udp_socket.settimeout(avg_time)
        sum_time = 0
        times = 0

"""Initialize connection with server"""
def init_connection():

    global udp_socket

    # create socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(0.003)

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

    while(1):
        send_time = time.time()
        udp_socket.sendto(packet_req, SERVER_ADDR)

        try:
            # wait for reply (JUST THE FD!)
            fd = struct.unpack('!i', udp_socket.recv(4))[0]
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            break
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Server failed to open/create a file. Try again!'

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

    packet_req = packet_struct.construct_read_packet(cur_req_num, fd, pos, n)

    # try to send the read request!
    while(1):
        send_time = time.time()
        udp_socket.sendto(packet_req, SERVER_ADDR)

        try:

            # wait for reply
            reply_packet = udp_socket.recv(1024)
            buf = struct.unpack('!1024s', reply_packet)[0].strip('\0')
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            break
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Server failed to read a file. Try again!'

    fd_pos[fd] += n
    return (buf, len(buf))

"""Write n bytes to fd starting from position fd_pos[fd]"""
def mynfs_write(fd, buf, n):

    global req_num

    variables_lock.acquire()
    pos = fd_pos[fd]
    req_num += 1
    cur_req_num = req_num
    variables_lock.release()

    packet_req = packet_struct.construct_write_packet(cur_req_num, fd, pos, cur_req_num, 1, buf)

    # try to send the write request!
    while(1):
        send_time = time.time()
        udp_socket.sendto(packet_req, SERVER_ADDR)

        try:

            # wait for reply
            reply_packet = struct.unpack('!i', udp_socket.recv(4))[0]
            print 'Got ack: {} for write request {}'.format(reply_packet, cur_req_num)
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            break
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Server failed to read a file. Try again!'

    # update pos of fd
    fd_pos[fd] += n
    return n

"""Change pointer's position in fd"""
def mynfs_seek(fd, pos):

    variables_lock.acquire()
    fd_pos[fd] = pos
    variables_lock.release()
