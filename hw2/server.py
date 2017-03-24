import socket
import struct
import sys
from packet_struct import *

DECODING='!16si'
TIMEOUT = 0.2

MULTI_IP = '224.3.29.71'
MULTI_PORT = 10000


# Tell the operating system to add the socket to the multicast group
# on all interfaces.
def socket_to_OS_multicast(sock):

    group = socket.inet_aton(MULTI_IP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)



udp_server_address = ('', MULTI_PORT)

# Create the UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
udp_sock.bind(udp_server_address)

#Update OS multicast group
socket_to_OS_multicast(udp_sock)

#Create the TCP socket
tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcp_socket.settimeout(TIMEOUT)

# Try to connect with a client
connection_complete = False
while (not connection_complete):
    print ('waiting to receive client from multicast!')
    packet, address = udp_sock.recvfrom(1024)
    ipaddr, port = deconstruct_packet(DECODING,packet)

    #remove null bytes!
    ipaddr = ipaddr.rstrip('\0')
    
    try:
        print 'Try connecting to IP: %s, port: %d' %(ipaddr,port)
        tcp_socket.connect((ipaddr,port))
        print 'Connection complete'   
        connection_complete = True
    except socket.timeout:
        print 'Trying again to connect!'

