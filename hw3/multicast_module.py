''' A module to handle multicast group '''

from packet_struct import *
import socket
import struct

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
def socket_to_OS_multicast_group(sock, multi_ip):

    group = socket.inet_aton(multi_ip)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Creates a socket to listen from multicast
def socket_for_multicast(multi_ip, multi_port):
    server_address = ('', multi_port)

    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to the server address
    sock.bind(server_address)

    #Update OS multicast group
    socket_to_OS_multicast_group(sock, multi_ip)
    return sock


'''
# Receive from multicast, return client address (IP,port) and service (svcid)
def receive_from_multicast(sock):

    #print ('waiting to receive client from multicast!')
    try:
        packet, address = sock.recvfrom(1024)
    except socket.timeout:
        return (None, None, None, None)
    ipaddr, port, svcid = deconstruct_packet(BROADCAST_ENCODING,packet)

    #remove null bytes!
    ipaddr = ipaddr.rstrip('\0')
    ipaddr = ipaddr.rstrip('\n')

    return (ipaddr, port, svcid, address[1])
'''
