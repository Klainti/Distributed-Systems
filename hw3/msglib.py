""" API for join/leave a group.Also send/receive msg from group chat.
    When join is called we create two threads. One listening to DIrSvc
    and one listening to multicast.

"""

import socket
import thread
import select
from packet_struct import *
from multicast_module import *

first_time = True

#The name the client has in each group chat
grp_info_my_name = {}

#The group info (ip, port) for every grp_socket
grp_sockets_grp_info = {}

#The group info (ip, port) for every service_socket
service_conn_grp_info = {}

total_service_conn = []
total_grp_sockets = []

# Services variables
service_addr = ()


#The messages received from multicast or DirSvc
messages = {}
messages_lock = thread.allocate_lock()

# Set the service address
def grp_setDir(diripaddr, dirport):

    global service_addr
    service_addr = (diripaddr, dirport)

# Join a group chat.
def grp_join(grp_ipaddr, grp_port, myid):

    global service_addr, service_conn, my_name, grp_socket, first_time

    #####################################
    s = socket.socket()
    s.connect(service_addr)

    request_for_grp = construct_join_packet(grp_ipaddr, grp_port, myid)

    # Send a request to connect
    s.send(request_for_grp)

    #Start the threads only the first time
    if (first_time):
        thread.start_new_thread (listen_from_DirSvc, ())
        first_time = False

    #Try till you get a valid socket
    grp_socket = -1
    while (grp_socket == -1):
        grp_socket = socket_for_multicast(grp_ipaddr, grp_port)

    #Update buffers
    grp_info_my_name[(grp_ipaddr, grp_port)] = myid
    service_conn_grp_info[s] = (grp_ipaddr, grp_port)
    grp_sockets_grp_info[grp_socket] = (grp_ipaddr, grp_port)
    messages[(grp_ipaddr, grp_port)] = []
    total_service_conn.append (s)

    return grp_socket

"""
    print "grp_info_my_name", grp_info_my_name
    print "service_conn_grp_info", service_conn_grp_info
    print "grp_sockets_grp_info", grp_sockets_grp_info
    print "messages", messages
"""

    #return grp_socket

# Leave a group.
def grp_leave(gsocket):

    #Get group chat info and the name he has
    grp_ipaddr = grp_sockets_grp_info[gsocket][0]
    grp_port = grp_sockets_grp_info[gsocket][1]
    my_name = grp_info_my_name[(grp_ipaddr, grp_port)]

    #Delete and close...

    print "Going to leave from group with ip", grp_ipaddr, "and port", grp_port

    request_for_dis = construct_join_packet(grp_ipaddr, grp_port, my_name)

    service_conn.send(request_for_dis)

    gsocket.close()



def listen_from_DirSvc ():

    global total_service_conn

    while (True):

        #Listen from all the service connections
        ready, _, _ = select.select (total_service_conn, [], [], 1)

        for service_conn in ready:

            packet = service_conn.recv(1024)
            name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, packet)

            name.strip('\0')

            #Find group info from service_conn_grp_info
            grp_ipaddr = service_conn_grp_info[service_conn][0]
            grp_port = service_conn_grp_info[service_conn][1]

            print "Received message for DirSvc"

            messages_lock.acquire()

            #Add the new message to the queue

            if (state == 1):
                messages[(grp_ipaddr, grp_port)].append (name + " is connected")
            elif (state == -1):
                #Break if it is ack for your exit
                if ( name == grp_info_my_name[(grp_ipaddr, grp_port)] ):
                    messages[(grp_ipaddr, grp_port)].append ("Disconnected from group chat successfully")
                    service_conn.close()
                    #Delete...
                    break

                messages[(grp_ipaddr, grp_port)].append (name + " is disconnected")

            print messages

            messages_lock.release()
