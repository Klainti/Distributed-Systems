''' A module to handle multicast group '''

from packet_struct import *
import socket


DECODING='!16si'
TIMEOUT = 0.2

MULTI_IP = '224.3.29.71'
MULTI_PORT = 10000

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
def socket_to_OS_multicast_group(sock):

    group = socket.inet_aton(MULTI_IP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Creates a socket to listen from multicast
def socket_for_multicast():
    server_address = ('', MULTI_PORT)

    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    # Bind to the server address
    sock.bind(server_address)

    #Update OS multicast group
    socket_to_OS_multicast_group(sock)
    return sock

# Receive from multicast, return client address (IP,port)
def receive_from_multicast(sock):

    print ('waiting to receive client from multicast!')
    packet, address = sock.recvfrom(1024)
    ipaddr, port = deconstruct_packet(DECODING,packet)

    #remove null bytes!
    ipaddr = ipaddr.rstrip('\0')

    return (ipaddr,port)



