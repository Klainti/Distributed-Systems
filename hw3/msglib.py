"""API for join/leave a group.Also send/receive msg from group chat."""

import socket
from packet_struct import *

service_addr = ()

# Set the service address
def grp_setDir(diripaddr, dirport):

    global service_addr
    service_addr = (diripaddr, dirport)

# Join a group chat.
def grp_join(grp_ipaddr, grp_port, myid):

    global service_addr

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tcp_socket.connect(service_addr)

    request_for_grp = construct_join_packet(grp_ipaddr, grp_port, myid)

    # Send a request to connect
    tcp_socket.send(request_for_grp)

    # wait service to confirm the joining the group chat.
    reply = tcp_socket.recv(1024)
    name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, reply)
    name.strip('\0')

    if (state == 1):
        print "{} is connected!".format(name)
        return tcp_socket
    else:
        return -1
