"""API for join/leave a group.Also send/receive msg from group chat."""

import socket
from packet_struct import *
from multicast_module import *

# Services variables
service_addr = ()
service_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Set the service address
def grp_setDir(diripaddr, dirport):

    global service_addr
    service_addr = (diripaddr, dirport)

# Join a group chat.
def grp_join(grp_ipaddr, grp_port, myid):

    global service_addr, service_conn

    service_conn.connect(service_addr)

    request_for_grp = construct_join_packet(grp_ipaddr, grp_port, myid)

    # Send a request to connect
    service_conn.send(request_for_grp)

    # wait service to confirm the joining the group chat.
    reply = service_conn.recv(1024)
    name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, reply)
    name.strip('\0')

    if (state == 1):
        print "{} is connected!".format(name)
        return socket_for_multicast(grp_ipaddr, grp_port)
    else:
        return -1

# Leave a group.
def grp_leave(gsocket):

    service_conn.send("Bye!")

    reply = service_conn.recv(1024)
    name, Type = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, reply)

    print name, Type
    if (Type == -1):
        print "Disconnect successfully"
        gsocket.close()
