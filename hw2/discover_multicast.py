import socket
import struct
import sys
from packet_struct import *


MULTI_IP = '224.3.29.71'
MULTI_PORT = 10000

ENCODING='!16si'
TIMEOUT = 0.2

def set_discover_multicast(ipaddr,port):

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
            packet = construct_packet(ENCODING,ipaddr,port)
            sent = udp_sock.sendto(packet,multicast_group)

            try:
                tcp_socket.listen(1)
                conn, addr = tcp_socket.accept()
                #conn.send ("Hello")
                print 'Connected at: %s' % str(addr)
                server_connection = True
            except socket.timeout:
                print 'Time out, no connection occur'
        finally:
            pass

    udp_sock.close()
    tcp_socket.close()

set_discover_multicast('127.0.0.1',0)
