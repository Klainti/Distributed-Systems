"""network file system API."""

import socket
import struct
import time
import threading

import packet_struct
import cache_API

# Global variables!
SERVER_ADDR = ()
udp_socket = None

# INIT VALUE OF TIMEOUT (ms)
TIMEOUT = 0.003
sum_time = 0
times = 0



variables_lock = threading.Lock()

# Pointer position for each file
fd_pos = {}

# counter for requests!
req_num = 0

# Freshness time for each file
freshness = {}

"""Update timeout of the udp socket"""
def update_timeout(new_time):

    global udp_socket, sum_time, times

    sum_time += new_time
    times += 1
    if (times >= 10):
        avg_time = max(0.003, round(float(sum_time/times), 4))
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


"""
    Internal function which send the read request and returns the data
    pos and size must be a multiple o BLOCK_SIZE
"""


def send_read_and_receive_data(fd, pos, size):

    global req_num

    received_data = {}

    variables_lock.acquire()
    cur_req_num = req_num
    req_num += 1
    variables_lock.release()


    packet_req = packet_struct.construct_read_packet(cur_req_num, fd, pos, size)

    # PHASE 1: Send the packet till you get the first reply packet
    while(1):

        # Send packet
        send_time = time.time()
        udp_socket.sendto(packet_req, SERVER_ADDR)

        # Wait for reply
        try:
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
            print 'Timeout'


    # Missing packets: so far all except the one we received
    missing_packets = [i for i in xrange(total)]
    missing_packets.remove(cur_num)

    received_data[cur_num] = data

    print "INTERNAL READ: Received data with number", cur_num, len(data)

    # PHASE 2: Try to receive the remaining packets
    print "INTERNAL READ: Gonna wait for other", total-1, "packets"

    # Try to receive the remaining packets of the reply
    for i in xrange(total-1):

        try:
            # wait for reply
            reply_packet = udp_socket.recv(1024)
            req_number, cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)
            if (req_number == cur_req_num and cur_num not in received_data):
                data = data.strip('\0')
                received_data[cur_num] = data
                missing_packets.remove(cur_num)
                print "INTERNAL READ: Received data with number", cur_num, len(data)
            rec_time = time.time()
            update_timeout(rec_time-send_time)
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Timeout'

    print "INTERNAL READ: Missing_packets: ", missing_packets

    # PHASE 3: Retry for missing packets


    print "INTERNAL READ: Retry for", len(missing_packets), "packets"

    while (missing_packets != []):

        size = packet_struct.BLOCK_SIZE

        start = 0
        end = 1

        # If missing sequential packets, send one big request
        while (end < len(missing_packets) and missing_packets[end] == missing_packets[end-1]+1):
            size += packet_struct.BLOCK_SIZE
            end += 1

        print "INTERNAL READ: Send again for data from", pos + missing_packets[start]*packet_struct.BLOCK_SIZE, "with size", size
        data = send_read_and_receive_data(fd, pos + missing_packets[start]*packet_struct.BLOCK_SIZE, size)

        piece = 0

        s = missing_packets[start]
        e = missing_packets[end-1] + 1

        # Update received_data
        for i in xrange(s, e):
            print "INTERNAL READ: Received part", i
            received_data[i] = data[piece: piece + packet_struct.BLOCK_SIZE]
            piece += packet_struct.BLOCK_SIZE
            missing_packets.remove(i)

        print "INTERNAL READ: Missing_packets: ", missing_packets

    print "INTERNAL READ: Received all parts"
    print received_data.keys()

    buf = ''

    for i in xrange (total):
        buf += received_data[i]

    return buf




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

        print "Send open request"
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
            print 'Timeout'

    variables_lock.acquire()
    fd_pos[fd] = 0
    freshness[fd] = cacheFreshnessT
    variables_lock.release()

    return fd


"""Read n bytes from fd starting from position fd_pos[fd]"""
def mynfs_read(fd, n):

    received_data = {}

    in_cache = [-1]

    # pos, size
    requests = []

    variables_lock.acquire()
    pos = fd_pos[fd]
    variables_lock.release()

    # Calculate the pos of the request based on BLOCK_SIZE
    new_pos = pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    offset = pos-new_pos

    # Calculate the size of the request based on BLOCK_SIZE
    size = max(1, n/packet_struct.BLOCK_SIZE) * packet_struct.BLOCK_SIZE
    if (size < n):
        size += packet_struct.BLOCK_SIZE


    for i in xrange(size/packet_struct.BLOCK_SIZE):
        found, data = cache_API.search_block(fd, new_pos+i*packet_struct.BLOCK_SIZE)
        if (found == True):
            received_data[i] = data
            in_cache.append(i)
    in_cache.append(size/packet_struct.BLOCK_SIZE)

    print "Already in cache:", in_cache

    for i in xrange(1, len(in_cache)):
        if (in_cache[i] > in_cache[i-1]+1):
            requests.append([new_pos + packet_struct.BLOCK_SIZE*(in_cache[i-1]+1), (in_cache[i]-in_cache[i-1]-1)*packet_struct.BLOCK_SIZE])

    print "Requests", requests

    for r in requests:

        data = send_read_and_receive_data(fd, r[0], r[1])

        for i in xrange(r[1]/packet_struct.BLOCK_SIZE):
            received_data[i + (r[0]-new_pos)/packet_struct.BLOCK_SIZE] = data[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE]

    # Construct reply
    buf = ''

    for i in xrange (size/packet_struct.BLOCK_SIZE):
        buf += received_data[i]

    buf = buf[offset:offset+n]

    # Update pointer
    variables_lock.acquire()
    fd_pos[fd] += len(buf)
    print "Set fd_pos to", fd_pos[fd]
    variables_lock.release()

    return buf


"""Write n bytes to fd starting from position fd_pos[fd]"""
def mynfs_write(fd, buf):

    global req_num

    n = len(buf)

    variables_lock.acquire()
    pos = fd_pos[fd]
    req_num += 1
    cur_req_num = req_num
    variables_lock.release()

    packets = []

    not_acked = []

    # Calculate the total number of packets need to be send
    num_of_packets = n/packet_struct.BLOCK_SIZE
    if (n%packet_struct.BLOCK_SIZE != 0):
        num_of_packets += 1

    for i in xrange(num_of_packets):
        packet_req = packet_struct.construct_write_packet(cur_req_num, fd, pos + i*packet_struct.BLOCK_SIZE, i, num_of_packets, buf[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE])
        packets.append(packet_req)
        print "Append/Send packet with data from", i*packet_struct.BLOCK_SIZE, "to", (i+1)*packet_struct.BLOCK_SIZE, "and pos", pos + i*packet_struct.BLOCK_SIZE
        udp_socket.sendto(packet_req, SERVER_ADDR)

    send_time = time.time()

    not_acked = [i for i in xrange(num_of_packets)]

    p = 0

    # try to send the write request!
    while(not_acked != []):

        try:
            # wait for reply
            req_num, packet_num = struct.unpack('!ii', udp_socket.recv(8))
            print 'Got ack: {} for write request {}'.format(packet_num, cur_req_num)
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            not_acked.remove(packet_num)
        except socket.timeout:

            rec_time = time.time()
            update_timeout(rec_time-send_time)

            print 'Not received ACK. Send packet', not_acked[p]

            udp_socket.sendto(packets[not_acked[p]], SERVER_ADDR)
            p = (p+1)%len(not_acked)
            send_time = time.time()




    # update pos of fd
    variables_lock.acquire()
    fd_pos[fd] += n
    variables_lock.release()

    return n



"""Change pointer's position in fd"""
def mynfs_seek(fd, pos):

    variables_lock.acquire()
    fd_pos[fd] = pos
    variables_lock.release()
