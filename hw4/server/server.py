"""Service support network file system."""

import sys
sys.path.append('../../hw4')

import socket
import struct
import os
import time
import threading

import packet_struct

# Global Variables
udp_socket = None

# counter of file descriptors!
c_fd = 0

# {key = a number: value= file descriptor}
fd_dict = {}


write_waiting = 0
wait_for_write_request = threading.Lock()
wait_for_write_request.acquire()

write_requests_lock = threading.Lock()
write_requests = []




read_waiting = 0
wait_for_read_request = threading.Lock()
wait_for_read_request.acquire()

read_requests_lock = threading.Lock()
# Client info, request number, fd, pos, length
read_requests = []



open_waiting = 0
wait_for_open_request = threading.Lock()
wait_for_open_request.acquire()

open_requests_lock = threading.Lock()
# Client info, request number, file name, create/open
open_requests = []

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

    threading.Thread(target=serve_open_request).start()
    threading.Thread(target=serve_read_request).start()
    threading.Thread(target=serve_write_request).start()

    print 'Service location: ({},{})'.format(MY_IP, udp_port)

"""Serves an open request"""
def serve_open_request():

    global c_fd, fd_dict, udp_socket, open_waiting


    while(True):

        open_requests_lock.acquire()

        if (len(open_requests) == 0):
            open_waiting = 1
            open_requests_lock.release()
            wait_for_open_request.acquire()
            open_requests_lock.acquire()

        new_request = open_requests[0]
        del open_requests[0]

        open_requests_lock.release()

        client_info = new_request[0]
        filename = new_request[1]
        create_open = new_request[2]

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

        "Send open reply"
        # notify client with file descriptor
        udp_socket.sendto(struct.pack('!i', c_fd), client_info)


"""Serves a read request"""
def serve_read_request():

    global udp_socket, read_waiting

    while(True):

        read_requests_lock.acquire()

        if (len(read_requests) == 0):
            read_waiting = 1
            read_requests_lock.release()
            wait_for_read_request.acquire()
            read_requests_lock.acquire()

        new_request = read_requests[0]
        del read_requests[0]

        read_requests_lock.release()

        client_info = new_request[0]
        fd = new_request[1]
        pos = new_request[2]
        length = new_request[3]

        print pos, length

        data = []

        local_fd = fd_dict[fd]

        # seek relative to the current position
        local_fd.seek(pos, 0)

        # get total reads!
        total_reads = int(length/packet_struct.BLOCK_SIZE)
        if (length % packet_struct.BLOCK_SIZE != 0):
            total_reads += 1

        # Get data
        for i in xrange(0, total_reads):
            buf = local_fd.read(packet_struct.BLOCK_SIZE)
            data.append(buf)
            # Reached EOF
            if (len(buf) == 0):
                total_reads = max(1, i)
                break

        print total_reads

        # Send total_reads packets
        for i in xrange(total_reads):
            if (i % 100 == 99):
                time.sleep(0.09)

            reply_packet = packet_struct.construct_read_rep_packet(i, total_reads, data[i])
            print "Send data", i+1, "/", total_reads, len(data[i]), len(reply_packet)

            # if (i%2 == 0):
            udp_socket.sendto(reply_packet, client_info)


"""Serves a write request"""
def serve_write_request():

    global udp_socket, write_waiting


    while(True):

        write_requests_lock.acquire()

        if (len(write_requests) == 0):
            write_waiting = 1
            write_requests_lock.release()
            wait_for_write_request.acquire()
            write_requests_lock.acquire()

        new_request = write_requests[0]
        del write_requests[0]

        write_requests_lock.release()

        client_info = new_request[0]
        fd = new_request[1]
        pos = new_request[2]
        data = new_request[3]
        size_of_data = new_request[4]

        print "packet len: ", size_of_data

        local_fd = fd_dict[fd]

        # seek relative to the current position
        local_fd.seek(pos, 0)

        print "Write at", pos, size_of_data

        local_fd.write(data)
        local_fd.flush()

       


"""Receive requests from clients!"""
def receive_from_clients():

    global udp_socket, open_waiting, read_waiting, write_waiting

    while(1):
        packet, client_info = udp_socket.recvfrom(1024)

        # Get only the type of the request!
        type_of_req = struct.unpack_from('!i', packet[:4])[0]

        if (type_of_req == packet_struct.OPEN_REQ):
            print "Got open request"

            create_open, filename = packet_struct.deconstruct_packet(packet_struct.OPEN_ENCODING, packet)[1:]
            filename =filename.strip('\0')

            # Update the list with open requests
            open_requests_lock.acquire()
            open_requests.append([client_info, filename, create_open])

            if (open_waiting == 1):
                open_waiting = 0
                wait_for_open_request.release()

            open_requests_lock.release()

        elif (type_of_req == packet_struct.READ_REQ):
            print "Got read request"

            fd, pos, length = packet_struct.deconstruct_packet(packet_struct.READ_REQ_ENCODING, packet)[1:]

            read_requests_lock.acquire()
            read_requests.append([client_info, fd, pos, length])

            if (read_waiting == 1):
                read_waiting = 0
                wait_for_read_request.release()

            read_requests_lock.release()

        elif (type_of_req == packet_struct.WRITE_REQ):
            print "Got write request"

            print "Send write reply"
            reply_packet = struct.pack('!i', 1)

            udp_socket.sendto(reply_packet, client_info)

            fd, pos, size_of_data, data = packet_struct.deconstruct_packet(packet_struct.WRITE_ENCODING, packet)[1:]
            data = data[:size_of_data]

            write_requests_lock.acquire()
            write_requests.append([client_info, fd, pos, data, size_of_data])

            if (write_waiting == 1):
                write_waiting = 0
                wait_for_write_request.release()

            write_requests_lock.release()

        else:
            pass

if __name__ == "__main__":
    init_srv()
    while(True):
        receive_from_clients()
