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
sum_time = 0
times = 0

CLOSE_TIMEOUT = 1000


send_read = threading.Lock()

# Pointer position for each file
fd_pos = {}

# Freshness time for each file
freshness = {}

# Last time we made a change (seek/write, read) to a file (fd)
last_time = {}

next_request_number = 0


# Custom ERROR
class TimeoutError(Exception):
    def __init__(self, message):
        self.message = message

# Custom ERROR
class FileError(Exception):
    def __init__(self, message):
        self.message = message


"""Update timeout of the udp socket"""


def update_timeout(new_time):

    pass
    #global udp_socket, sum_time, times

    #sum_time += new_time
    #times += 1
    #if (times >= 10):
        #avg_time = max(0.03, round(float(sum_time/times), 4))
        # print "AVG TIME: {}".format(avg_time)
        #udp_socket.settimeout(avg_time)
        #TIMEOUT = avg_time
        #sum_time = 0
        #times = 0


"""Initialize connection with server"""


def init_connection():

    global udp_socket

    # create socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(0.09)

    # start nfs threads!
    cache_API.init_cache()


"""
    Internal function which send the read request and returns the data
    pos and size must be a multiple o BLOCK_SIZE
"""


def send_read_and_receive_data(fd, pos, size):

    global udp_socket, next_request_number

    send_read.acquire()


    udp_socket.settimeout(0.005)


    buf = ""

    packets = size/packet_struct.BLOCK_SIZE
    if (size%packet_struct.BLOCK_SIZE != 0):
        packets += 1

    print "Read", packets

    for i in xrange(packets):

        next_request_number += 1

        packet_req = packet_struct.construct_read_packet(next_request_number, fd, pos + i*packet_struct.BLOCK_SIZE, packet_struct.BLOCK_SIZE)

        resend = True

        while(True):

            try:

                if (resend):
                    resend = False
                    udp_socket.sendto(packet_req, SERVER_ADDR)


                reply_packet = udp_socket.recv(packet_struct.READ_REP_SIZE)

                # Received older packet
                if (len(reply_packet) != packet_struct.READ_REP_SIZE):
                    continue

                returned_request_number, cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)

                # Received older packet
                if (returned_request_number != next_request_number):
                    continue

                if (length == 0):
                    print "EOF", next_request_number
                    break

                data = data[:length]

                buf += data

                break

            except socket.timeout:
                resend = True


    send_read.release()

    print len(buf)

    return buf

'''
    print "Send read", pos, size

    received_data = {}

    packet_req = packet_struct.construct_read_packet(fd, pos, size)

    udp_socket.settimeout(size/packet_struct.BLOCK_SIZE * 0.005)

    old_transmit = False

    # PHASE 1: Send the packet till you get the first reply packet
    while(1):

        # Send packet
        if (not old_transmit):
            old_transmit = False
            print "Send read request"
            send_time = time.time()
            udp_socket.sendto(packet_req, SERVER_ADDR)

        # Wait for reply
        try:
            reply_packet = udp_socket.recv(packet_struct.READ_REP_SIZE)

            print "Received first", len(reply_packet)

            if (len(reply_packet) != packet_struct.READ_REP_SIZE and len(reply_packet) > 0):
                old_transmit = True
                continue

            cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)

            data = data[:length]
            rec_time = time.time()
            update_timeout(rec_time-send_time)

            break
        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)

    # Missing packets: so far all except the one we received
    missing_packets = [i for i in xrange(total)]
    missing_packets.remove(cur_num)

    received_data[cur_num] = data

    # PHASE 2: Try to receive the remaining packets

    # Try to receive the remaining packets of the reply

    udp_socket.settimeout(0.0005)

    print "wait for", total-1
    i = 0
    while (i < total-1):

        i += 1

        try:

            # wait for reply
            reply_packet = udp_socket.recv(packet_struct.READ_REP_SIZE)

            if (len(reply_packet) == packet_struct.READ_REP_SIZE):

                cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)

                if (cur_num not in received_data):
                    # print "Received", cur_num, i
                    data = data[:length]
                    received_data[cur_num] = data
                    try:
                        missing_packets.remove(cur_num)
                    except ValueError:
                        pass

                rec_time = time.time()
                update_timeout(rec_time-send_time)

        except socket.timeout:
            rec_time = time.time()
            update_timeout(rec_time-send_time)

    # PHASE 3: Retry for missing packets

    print "Missing", missing_packets, len(missing_packets)

    while (missing_packets != []):

        size = packet_struct.BLOCK_SIZE

        start = 0
        end = 1

        # If missing sequential packets, send one big request
        while (end < len(missing_packets) and missing_packets[end] == missing_packets[end-1]+1):
            size += packet_struct.BLOCK_SIZE
            end += 1

        send_read.release()
        data = send_read_and_receive_data(fd, pos + missing_packets[start]*packet_struct.BLOCK_SIZE, size)
        send_read.acquire()

        piece = 0

        s = missing_packets[start]
        e = missing_packets[end-1] + 1

        # Update received_data
        for i in xrange(s, e):
            received_data[i] = data[piece: piece + packet_struct.BLOCK_SIZE]
            piece += packet_struct.BLOCK_SIZE
            missing_packets.remove(i)

    buf = ''

    for i in xrange(total):
        try:
            buf += received_data[i]
        except KeyError:
            continue


    send_read.release()

    return buf

'''


"""Set SERVER INFO"""


def mynfs_setSrv(ipaddr, port):

    global SERVER_ADDR

    # stores info for server
    SERVER_ADDR = (ipaddr, port)

    init_connection()

    return 1


"""Send Open request"""


def mynfs_open(fname, create, cacheFreshnessT):

    global udp_socket, next_request_number

    next_request_number += 1

    # create and send the open request!
    packet_req = packet_struct.construct_open_packet(next_request_number, create, fname)

    resend = True

    while(1):

        if (resend):
            resend = False
            print "Send open request"
            send_time = time.time()
            udp_socket.sendto(packet_req, SERVER_ADDR)

        try:

            reply_packet = udp_socket.recv(packet_struct.READ_REP_SIZE)

            if (len(reply_packet) != 8):
                continue

            returned_request_number, fd = struct.unpack('!ii', reply_packet)

            if (returned_request_number != next_request_number):
                continue

            rec_time = time.time()
            update_timeout(rec_time-send_time)
            break

        except socket.timeout:
            resend = True
            rec_time = time.time()
            update_timeout(rec_time-send_time)

    fd_pos[fd] = 0
    freshness[fd] = cacheFreshnessT
    last_time[fd] = time.time()

    return fd


"""Read n bytes from fd starting from position fd_pos[fd]"""


def mynfs_read(fd, n):

    received_data = {}

    # pos, size
    requests = []

    if (fd not in fd_pos.keys()):
        raise FileError, ("Unknown file descriptor")
        return

    if (time.time() - last_time[fd] > CLOSE_TIMEOUT):

        cache_API.delete_blocks(fd)

        del fd_pos[fd]
        del freshness[fd]
        del last_time[fd]
        raise TimeoutError("Last access in file long ago")
        return

    last_time[fd] = time.time()

    pos = fd_pos[fd]

    # Calculate the pos of the request based on BLOCK_SIZE
    new_pos = pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    offset = pos-new_pos

    # Calculate the size of the request based on BLOCK_SIZE
    size = max(1, n/packet_struct.BLOCK_SIZE) * packet_struct.BLOCK_SIZE
    if (size < n):
        size += packet_struct.BLOCK_SIZE

    # First check if the begining of the data requested are in cache
    buf = ""
    in_cache_size = 0
    found, data = cache_API.search_block(fd, new_pos)

    if (found):

        print "Start in cache"

        while (found and in_cache_size <= size):
            buf += data
            new_pos += packet_struct.BLOCK_SIZE
            in_cache_size += packet_struct.BLOCK_SIZE

            found, data = cache_API.search_block(fd, new_pos)

        buf = buf[offset:offset+n]

        # Update pointer
        fd_pos[fd] += len(buf)
        print "Set fd_pos to", fd_pos[fd]

        return buf

    # If the begining not in cache must send read request at server


    in_cache = [new_pos/packet_struct.BLOCK_SIZE - 1]

    pieces = size/packet_struct.BLOCK_SIZE
    if (size%packet_struct.BLOCK_SIZE != 0):
        pieces += 1

    # First check if any parts are in the cache
    for i in xrange(pieces):

        found, data = cache_API.search_block(fd, new_pos+i*packet_struct.BLOCK_SIZE)

        if (found):

            received_data[i] = data
            in_cache.append(i)

            # If length of data in cache are less than BLOCK_SIZE => EOF
            if (len(data) < packet_struct.BLOCK_SIZE):
                pieces = i+1
                break

    in_cache.append(pieces)

    print "Already in cache:", in_cache

    for i in xrange(1, len(in_cache)):
        if (in_cache[i] > in_cache[i-1]+1):
            requests.append([packet_struct.BLOCK_SIZE*(in_cache[i-1]+1), (in_cache[i]-in_cache[i-1]-1)*packet_struct.BLOCK_SIZE])

    print "Requests", requests

    # Then send requests for the missing parts
    for r in requests:

        data = send_read_and_receive_data(fd, r[0], r[1])

        print "Received length", len(data)

        for i in xrange(r[1]/packet_struct.BLOCK_SIZE):
            received_data[i + (r[0]-new_pos)/packet_struct.BLOCK_SIZE] = data[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE]

    print "Buffer pieces", len(received_data)

    # Construct reply
    buf = ''

    for i in xrange(len(received_data)):

        buf += received_data[i]

        if (received_data[i] != "" and i not in in_cache):
            cache_API.insert_block(fd, new_pos + i*packet_struct.BLOCK_SIZE, received_data[i], freshness[fd])

    print "Buffer length before offset", len(buf)

    buf = buf[offset:offset+n]

    print "Buffer length after offset", len(buf)

    # Update pointer
    fd_pos[fd] += len(buf)
    print "Set fd_pos to", fd_pos[fd]

    return buf


"""Write n bytes to fd starting from position fd_pos[fd]"""


def mynfs_write(fd, buf):

    global udp_socket, next_request_number

    if (fd not in fd_pos.keys()):
        raise FileError, ("Unknown file descriptor")
        return

    if (time.time() - last_time[fd] > CLOSE_TIMEOUT):

        cache_API.delete_blocks(fd)

        del fd_pos[fd]
        del freshness[fd]
        del last_time[fd]

        raise TimeoutError, ("Last access in file long ago")

        return

    last_time[fd] = time.time()

    pos = fd_pos[fd]

    n = len(buf)

    print "Write from", pos, len(buf)

    # ................ PHASE 1: Find the data before and after buf so len(total_data)%BLOCK_SIZE == 0 ................ #

    # Find the data before the write position in the current block
    start_pos = pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    start_offset = pos - start_pos

    print "Block starts at", start_pos

    data = ""

    if (start_offset > 0):
        print "Get the previous data"
        found, data = cache_API.search_block(fd, start_pos)
        if (not found):
            data = send_read_and_receive_data(fd, start_pos, packet_struct.BLOCK_SIZE)
        data = data[:start_offset]

    new_data = data + buf

    # Find the data after the write in the last block
    end_pos = pos + n

    end_pos = end_pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    end_offset = pos + n - end_pos

    data = ""

    if (end_offset > 0):
        print "Get the next data"
        found, data = cache_API.search_block(fd, end_pos)
        if (not found):
            data = send_read_and_receive_data(fd, end_pos, packet_struct.BLOCK_SIZE)
        data = data[end_offset:]

    # New data to be writen + starting data + ending data
    new_data = new_data + data

    # Calculate the total number of packets need to be send
    num_of_packets = n/packet_struct.BLOCK_SIZE
    if (n % packet_struct.BLOCK_SIZE != 0):
        num_of_packets += 1

    # Add new blocks to cache
    for i in xrange(num_of_packets):
        cache_API.insert_block(fd, start_pos + i*packet_struct.BLOCK_SIZE, new_data[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE], freshness[fd])

    # ................ PHASE 2: Send changes over network ................ #

    print "Total write packets: ", num_of_packets

    total_sends = 0
    total_acks = 0
    timeouts = 0

    #################################################################
    udp_socket.settimeout(0.09)
    #################################################################

    for i in xrange(num_of_packets):

        next_request_number += 1

        packet_req = packet_struct.construct_write_packet(next_request_number, fd, pos + i*packet_struct.BLOCK_SIZE, buf[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE])

        resend = True

        while(True):

            try:


                if (resend):
                    resend = False
                    udp_socket.sendto(packet_req, SERVER_ADDR)

                send_time = time.time()

                ack = udp_socket.recv(packet_struct.READ_REP_SIZE)

                # Received a packet from an older transmission
                if (len(ack) != 4):
                    continue

                returned_request_number = struct.unpack('!i', ack)[0]

                # Received a packet from an older transmission
                if (returned_request_number != next_request_number):
                    continue

                rec_time = time.time()
                update_timeout(rec_time-send_time)

                break

            except socket.timeout:

                resend = True

                rec_time = time.time()
                update_timeout(rec_time-send_time)
                timeouts += 1


    # update pos of fd
    fd_pos[fd] += n

    print "Write complete", timeouts

    return n


"""Change pointer's position in fd"""


def mynfs_seek(fd, pos):

    if (fd not in fd_pos.keys()):
        raise FileError,("Unknown file descriptor")
        return

    if (time.time() - last_time[fd] > CLOSE_TIMEOUT):

        cache_API.delete_blocks(fd)

        del fd_pos[fd]
        del freshness[fd]
        del last_time[fd]
        raise TimeoutError,("Last access in file long ago")
        return

    fd_pos[fd] = pos
