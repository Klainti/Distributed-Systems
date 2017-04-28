"""A service that supports group chats.

Accept members and puts them in their appropriate group chat
Also, the service notifies others members that are already in a group chat
about joining/leaving of a member!
"""

import socket
from packet_struct import *

MY_IP = "127.0.0.1"

msggroup_sockets = {}


tcp_port = 0
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind((MY_IP, tcp_port))
tcp_port = tcp_socket.getsockname()[1]

print 'Service location: ({},{})'.format(MY_IP, tcp_port)

while (True):

    # Wait for new connection
    tcp_socket.listen(1)
    conn, addr = tcp_socket.accept()

    # Wait for group chat and member info
    member_info_packet = conn.recv(1024)
    grpip, grpport, name = deconstruct_packet(JOIN_ENCODING, member_info_packet)

    grpip = grpip.strip('\0')
    name = name.strip('\0')

    new_member_packet = construct_member_packet(name, 1)

    if ((grpip, grpport) not in msggroup_sockets):
        # First member init the group chat
        msggroup_sockets[(grpip, grpport)] = [(conn, name)]
    else:

        # Send to everyone that the member with name is connected
        for member in msggroup_sockets[(grpip, grpport)]:
            member[0].send(new_member_packet)

        # Add member to dictionary
        msggroup_sockets[(grpip, grpport)].append((conn, name))

    print msggroup_sockets

    # Send that it is connected to the group chat
    conn.send(new_member_packet)
