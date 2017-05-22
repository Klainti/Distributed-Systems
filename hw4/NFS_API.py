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

    received_data = {}

    variables_lock.acquire()
    pos = fd_pos[fd]
    req_num += 1
    cur_req_num = req_num
    variables_lock.release()

    size = max(1, n/packet_struct.BLOCK_SIZE) * packet_struct.BLOCK_SIZE
    if (size < n):
        size += packet_struct.BLOCK_SIZE

    print "Gonna send read request for", size

    packet_req = packet_struct.construct_read_packet(cur_req_num, fd, pos, size)

    # try to send the read request!
    while(1):
        send_time = time.time()
        udp_socket.sendto(packet_req, SERVER_ADDR)

        try:

            # wait for reply
            reply_packet = udp_socket.recv(1024)
            req_number, cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)
            if (req_number == cur_req_num):
                data = data.strip('\0')
                rec_time = time.time()
                update_timeout(rec_time-send_time)
                break
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Server failed to read a file. Try again!'

    missing_packets = [i for i in xrange(total)]
    received_data[cur_num] = data
    print "Received", data, "with number", cur_num
    missing_packets.remove(cur_num)

    print "Gonna wait for other", total-1, "packets"

    for i in xrange(total-1):

        try:
            # wait for reply
            reply_packet = udp_socket.recv(1024)
            req_number, cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)
            if (cur_num not in received_data):
                data = data.strip('\0')
                received_data[cur_num] = data
                missing_packets.remove(cur_num)
                print "Received", data, "with number", cur_num
            rec_time = time.time()
            update_timeout(rec_time-send_time)
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Server failed to read a file. Try again!'

    print "Missing_packets: ", missing_packets

    # Send new read requests for missing packets
    pos = 0

    while (missing_packets != []):

        size = packet_struct.BLOCK_SIZE

        start = pos
        pos += 1

        # If missing sequential packets, send one big request
        while (pos < len(missing_packets) and missing_packets[pos] == missing_packets[pos-1]):
            size += packet_struct.BLOCK_SIZE
            pos += 1

        data = mynfs_read(fd, size)

        piece = 0

        s = missing_packets[start]
        e = missing_packets[pos]

        # Update received_data
        for i in xrange(s, e):
            received_data[i] = data[piece: piece + packet_struct.BLOCK_SIZE]
            piece += packet_struct.BLOCK_SIZE
            missing_packets.remove(i)

        print "Missing_packets: ", missing_packets

    print "Received all parts"
    print received_data

    # Construct reply
    buf = ''

    for i in xrange (total):
        buf += received_data[i]

    return buf[:n]


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
