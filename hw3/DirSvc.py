import socket
from packet_struct import *

MY_IP = ""

msggroup_sockets = {}


tcp_port = 0
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind((MY_IP, tcp_port))
tcp_port = tcp_socket.getsockname()[1]


while (True):


    #Wait for new connection
    tcp_socket.listen (1)
    conn, addr = tcp_socket.accept()

    #Wait for group chat and member info
    packet = conn.recv ()
    grpip, grpport, name = deconstruct_packet ()

    packet = construct_member_packet (name, 1)

    if ([grpip, grpport] not in msggroup_sockets):
        msggroup_sockets[ [grpip, grpport] ] = [ [conn, name] ]
    else:

        #Send to everyone that the member with name is connected
        for member in msggroup_sockets[ [grpip, grpport] ]:
            member[0].send (packet)

        #Add member to dictionary
        msggroup_sockets[ [grpip, grpport] ].append ([conn, name])

    #Send that it is connected to the group chat
    conn.send (packet)
