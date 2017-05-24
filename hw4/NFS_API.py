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

    # Calculate the pos of the request based on BLOCK_SIZE
    new_pos = pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    offset = pos-new_pos

    # Calculate the size of the request based on BLOCK_SIZE
    size = max(1, n/packet_struct.BLOCK_SIZE) * packet_struct.BLOCK_SIZE
    if (size < n):
        size += packet_struct.BLOCK_SIZE

    print "Gonna send read request for", size, "from", new_pos

    # Construct packet
    packet_req = packet_struct.construct_read_packet(cur_req_num, fd, new_pos, size)

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
            print 'Timeout'

    missing_packets = [i for i in xrange(total)]
    received_data[cur_num] = data
    print "Received data with number", cur_num, len(data)
    missing_packets.remove(cur_num)

    print "Gonna wait for other", total-1, "packets"

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
                print "Received data with number", cur_num, len(data)
            rec_time = time.time()
            update_timeout(rec_time-send_time)
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)
            print 'Timeout'

    print "Missing_packets: ", missing_packets

    # Send new read requests for missing packets
    p = 0

    print "Retry for", len(missing_packets), "packets"
    while (missing_packets != []):

        size = packet_struct.BLOCK_SIZE

        start = pos
        p += 1

        # If missing sequential packets, send one big request
        while (p < len(missing_packets) and missing_packets[p] == missing_packets[p-1]):
            size += packet_struct.BLOCK_SIZE
            p += 1

        data = mynfs_read(fd, size)

        piece = 0

        s = missing_packets[start]
        e = missing_packets[p]

        # Update received_data
        for i in xrange(s, e):
            received_data[i] = data[piece: piece + packet_struct.BLOCK_SIZE]
            piece += packet_struct.BLOCK_SIZE
            missing_packets.remove(i)

        print "Missing_packets: ", missing_packets

    print "Received all parts"
    print received_data.keys()

    # Construct reply
    buf = ''

    for i in xrange (total):
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
