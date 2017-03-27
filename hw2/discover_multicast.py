import socket
import struct
import sys
import thread
import time
from packet_struct import *


MULTI_IP = '224.3.29.71'
MULTI_PORT = 10000

ENCODING='!16sii'
TIMEOUT = 0.2

server_list = {}
server_list_lock = thread.allocate_lock()

def send_data(svcid):

    s_time = float(raw_input("Sleep time > "))

    while(1):

        server_list_lock.acquire()
        if (svcid in server_list.keys()):
            tmp_list = server_list[svcid]
        else:
            tmp_list = []
        server_list_lock.release()

        for s in tmp_list:
            time.sleep(s_time)
            s.send('Hello from %d' % s.getsockname()[1])

# Add a server to t server_list
def add_server(svcid,socket):

    # check service already has at least one server!
    if (svcid in server_list.keys()):
        server_list[svcid].append(socket)
    else:
        server_list[svcid] = [socket]

    print server_list

def set_discover_multicast(ipaddr,port,svcid):

    multicast_group = (MULTI_IP,MULTI_PORT)

    #Create the datagram socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #Create TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((ipaddr,port))
    port = tcp_socket.getsockname()[1]
    tcp_socket.settimeout(TIMEOUT)

    server_connection = False
    while(not server_connection):

        try:
            #Send data to the multicast group
            print 'Sending IP: %s and port: %d' % (ipaddr,port)
            packet = construct_packet(ENCODING,ipaddr,port,svcid)
            sent = udp_sock.sendto(packet,multicast_group)

            try:
                tcp_socket.listen(1)
                conn, addr = tcp_socket.accept()
                conn.send('Hello')

                server_list_lock.acquire()
                add_server(svcid,conn)
                server_list_lock.release()

                print 'Connected at: %s' % str(addr)
                server_connection = True
            except socket.timeout:
                print 'Time out, no connection occur'
        finally:
            pass

thread.start_new_thread(send_data,(1,))
set_discover_multicast('127.0.0.1',0,1)
while(1):
    pass
