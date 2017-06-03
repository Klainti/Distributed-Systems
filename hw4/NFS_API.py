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

    global udp_socket, sum_time, times

    sum_time += new_time
    times += 1

    if (times >= 50):
        avg_time = max(0.03, float(sum_time/times))

        udp_socket.settimeout(avg_time)

        TIMEOUT = avg_time

        sum_time = 0
        times = 0


"""Initialize connection with server"""


def init_connection():

    global udp_socket

    # create socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(0.1)

    # start nfs threads!
    cache_API.init_cache()


"""
    Internal function which send the read request and returns the data
    pos and size must be a multiple o BLOCK_SIZE
"""


def send_read_and_receive_data(fd, pos, size):

    global udp_socket, next_request_number

    timeouts = 0

    send_read.acquire()


    udp_socket.settimeout(0.1)


    buf = ""

    packets = size/packet_struct.BLOCK_SIZE
    if (size%packet_struct.BLOCK_SIZE != 0):
        packets += 1

    for i in xrange(packets):

        next_request_number += 1

        packet_req = packet_struct.construct_read_packet(next_request_number, fd, pos + i*packet_struct.BLOCK_SIZE, packet_struct.BLOCK_SIZE)

        resend = True

        while(True):

            try:

                if (resend):

                    stime = time.time()

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
                    break

                update_timeout(time.time() - stime)

                data = data[:length]

                buf += data

                break

            except socket.timeout:
                resend = True
                timeouts += 1

                update_timeout(time.time() - stime)

    send_read.release()

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

    global udp_socket, next_request_number

    next_request_number += 1

    # create and send the open request!
    packet_req = packet_struct.construct_open_packet(next_request_number, create, fname)

    resend = True

    while(1):

        if (resend):

            stime = time.time()

            resend = False
            udp_socket.sendto(packet_req, SERVER_ADDR)

        try:

            reply_packet = udp_socket.recv(packet_struct.READ_REP_SIZE)

            if (len(reply_packet) != 8):
                continue

            returned_request_number, fd = struct.unpack('!ii', reply_packet)

            if (returned_request_number != next_request_number):
                continue

            update_timeout(time.time() - stime)
            break

        except socket.timeout:
            resend = True
            update_timeout(time.time() - stime)

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

        while (found and in_cache_size <= size):
            buf += data
            new_pos += packet_struct.BLOCK_SIZE
            in_cache_size += packet_struct.BLOCK_SIZE

            found, data = cache_API.search_block(fd, new_pos)

        buf = buf[offset:offset+n]

        # Update pointer
        fd_pos[fd] += len(buf)

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

    for i in xrange(1, len(in_cache)):
        if (in_cache[i] > in_cache[i-1]+1):
            requests.append([packet_struct.BLOCK_SIZE*(in_cache[i-1]+1), (in_cache[i]-in_cache[i-1]-1)*packet_struct.BLOCK_SIZE])

    # Then send requests for the missing parts
    for r in requests:

        data = send_read_and_receive_data(fd, r[0], r[1])

        for i in xrange(r[1]/packet_struct.BLOCK_SIZE):
            received_data[i + (r[0]-new_pos)/packet_struct.BLOCK_SIZE] = data[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE]

    # Construct reply
    buf = ''

    for i in xrange(len(received_data)):

        buf += received_data[i]

        if (received_data[i] != "" and i not in in_cache):
            cache_API.insert_block(fd, new_pos + i*packet_struct.BLOCK_SIZE, received_data[i], freshness[fd])

    buf = buf[offset:offset+n]

    # Update pointer
    fd_pos[fd] += len(buf)

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

    # ................ PHASE 1: Find the data before and after buf so len(total_data)%BLOCK_SIZE == 0 ................ #

    # Find the data before the write position in the current block
    start_pos = pos/packet_struct.BLOCK_SIZE * packet_struct.BLOCK_SIZE
    start_offset = pos - start_pos

    data = ""

    if (start_offset > 0):
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

    total_sends = 0
    total_acks = 0
    timeouts = 0

    #################################################################
    udp_socket.settimeout(0.1)
    #################################################################

    for i in xrange(num_of_packets):

        next_request_number += 1

        packet_req = packet_struct.construct_write_packet(next_request_number, fd, pos + i*packet_struct.BLOCK_SIZE, buf[i*packet_struct.BLOCK_SIZE: (i+1)*packet_struct.BLOCK_SIZE])

        resend = True

        while(True):

            try:


                if (resend):

                    stime = time.time()

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

                update_timeout(time.time() - stime)

                break

            except socket.timeout:

                resend = True

                update_timeout(time.time() - stime)

                timeouts += 1

    # update pos of fd
    fd_pos[fd] += n

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


"""Close a file (locally)"""


def mynfs_close(fd):

    if (fd not in fd_pos.keys()):
        raise FileError,("Unknown file descriptor")
        return

    del fd_pos[fd]
    del freshness[fd]
    del last_time[fd]

    return
