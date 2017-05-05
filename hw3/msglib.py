""" API for join/leave a group.Also send/receive msg from group chat.
    When join is called we create two threads. One listening to DIrSvc
    and one listening to multicast.

"""

import socket
import thread
import select
import time
from packet_struct import *
from multicast_module import *

first_time = True


buffers_lock = thread.allocate_lock()

# The name the client has in each group chat
grp_info_my_name = {}
# The group info (ip, port) for every grp_socket
grp_sockets_grp_info = {}
# The group socket for every group
grp_info_grp_sockets = {}
# The group info (ip, port) for every service_socket
service_conn_grp_info = {}
# All service connections and all multicast connections
total_service_conn = []
total_grp_sockets = []
# The members of each group
grp_info_members = {}

last_received_seq_number = {}

next_seq_number = {}

# Services variables
service_addr = ()

# The messages received from multicast
recv_messages = {}
recv_messages_lock = thread.allocate_lock()

# The messages which are going to be send
send_messages = {}
send_messages_lock = thread.allocate_lock()

# The messages received from DirSvc
service_messages = {}
service_messages_lock = thread.allocate_lock()

# ............................. <API> ............................. #


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

    buffers_lock.acquire()

    grp_info_members[(grp_ipaddr, grp_port)] = []

    while (True):

        packet = s.recv(1024)

        name = deconstruct_packet(PREVIOUS_MEMBERS_ENCODING, packet)[0]
        name = name.strip('\0')

        if (name == myid):
            break

        grp_info_members[(grp_ipaddr, grp_port)].append(name)

    print "Already connected members: ", grp_info_members

    buffers_lock.release()

    # Start the threads only the first time
    if (first_time):
        thread.start_new_thread(listen_from_DirSvc, ())
        thread.start_new_thread(listen_from_multicast, ())
        thread.start_new_thread(send_to_multicast, ())
        first_time = False

    # Try till you get a valid socket
    grp_socket = -1
    while (grp_socket == -1):
        grp_socket = socket_for_multicast(grp_ipaddr, grp_port)

    buffers_lock.acquire()

    # Update buffers
    grp_info_my_name[(grp_ipaddr, grp_port)] = myid
    service_conn_grp_info[s] = (grp_ipaddr, grp_port)
    grp_sockets_grp_info[grp_socket] = (grp_ipaddr, grp_port)
    grp_info_grp_sockets[(grp_ipaddr, grp_port)] = grp_socket
    last_received_seq_number[(grp_ipaddr, grp_port)] = 0
    next_seq_number[(grp_ipaddr, grp_port)] = 1

    total_service_conn.append(s)
    total_grp_sockets.append(grp_socket)

    recv_messages_lock.acquire()
    recv_messages[(grp_ipaddr, grp_port)] = {}
    recv_messages_lock.release()

    send_messages_lock.acquire()
    send_messages[(grp_ipaddr, grp_port)] = []
    send_messages_lock.release()

    service_messages_lock.acquire()
    service_messages[(grp_ipaddr, grp_port)] = []
    service_messages_lock.release()



    buffers_lock.release()

    return grp_socket


# Leave a group.
def grp_leave(gsocket):

    # Get group chat info and the name he has

    buffers_lock.acquire()

    grp_ipaddr = grp_sockets_grp_info[gsocket][0]
    grp_port = grp_sockets_grp_info[gsocket][1]
    my_name = grp_info_my_name[(grp_ipaddr, grp_port)]

    service_conn = None

    for s in service_conn_grp_info.keys():
        if (service_conn_grp_info[s] == (grp_ipaddr, grp_port)):
            service_conn = s
            break

    buffers_lock.release()

    # Delete and close...

    request_for_dis = construct_join_packet(grp_ipaddr, grp_port, my_name)

    service_conn.send(request_for_dis)

    gsocket.close()


# Return the next message
def grp_recv(gsocket):


    # Get group info
    buffers_lock.acquire()
    grp_ipaddr = grp_sockets_grp_info[gsocket][0]
    grp_port = grp_sockets_grp_info[gsocket][1]
    buffers_lock.release()

    # The message which is returned
    m = ""
    t = 0

    while (m == ""):

        # First check service_messages
        service_messages_lock.acquire()
        if (len(service_messages[(grp_ipaddr, grp_port)]) > 0):
            m = service_messages[(grp_ipaddr, grp_port)][0][0]
            t = service_messages[(grp_ipaddr, grp_port)][0][1]
            del service_messages[(grp_ipaddr, grp_port)][0]
            service_messages_lock.release()
            break
        else:

            service_messages_lock.release()

            # Then check group messages

            # Prepei na elegxw an einai kai to epomeno mesa

            recv_messages_lock.acquire()
            if (next_seq_number[(grp_ipaddr, grp_port)] in recv_messages[(grp_ipaddr, grp_port)]):
                m = recv_messages[(grp_ipaddr, grp_port)][next_seq_number[(grp_ipaddr, grp_port)]]
                t = 0
                next_seq_number[(grp_ipaddr, grp_port)] += 1
                # del recv_messages[(grp_ipaddr, grp_port)][next_seq_number]
                recv_messages_lock.release()
                break

            recv_messages_lock.release()

        time.sleep(0.05)

    return m, t


# Add to send_messages the new message
def grp_send(gsocket, message):

    # Get group info
    buffers_lock.acquire()
    grp_ipaddr = grp_sockets_grp_info[gsocket][0]
    grp_port = grp_sockets_grp_info[gsocket][1]
    buffers_lock.release()

    send_messages_lock.acquire()
    send_messages[(grp_ipaddr, grp_port)].append(message)
    send_messages_lock.release()

# ............................. </API> ............................. #


# ............................. <THREADS> ............................. #


# The thread which receives messages from DirSvc
def listen_from_DirSvc():

    global total_service_conn

    while (True):

        buffers_lock.acquire()
        current_service_conn = total_service_conn
        buffers_lock.release()

        # Listen from all the service connections
        ready, _, _ = select.select(current_service_conn, [], [], 1)

        for service_conn in ready:

            packet = service_conn.recv(1024)
            name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, packet)

            name = name.strip('\0')

            # Find group info from service_conn_grp_info
            buffers_lock.acquire()
            grp_ipaddr = service_conn_grp_info[service_conn][0]
            grp_port = service_conn_grp_info[service_conn][1]
            buffers_lock.release()

            # print "Received message for DirSvc"

            # Add the new message to the queue
            service_messages_lock.acquire()

            if (state == 1):
                service_messages[(grp_ipaddr, grp_port)].append([name + " is connected", 1])

                buffers_lock.acquire()
                grp_info_members[(grp_ipaddr, grp_port)].append(name)
                print grp_info_members
                buffers_lock.release()

            elif (state == -1):
                buffers_lock.acquire()

                grp_info_members[(grp_ipaddr, grp_port)].remove(name)
                print grp_info_members

                if (name == grp_info_my_name[(grp_ipaddr, grp_port)]):
                    service_messages[(grp_ipaddr, grp_port)].append(["Disconnected from group chat successfully", -2])
                    service_conn.close()
                    # Delete...

                buffers_lock.release()

                service_messages[(grp_ipaddr, grp_port)].append([name + " is disconnected", -1])

            # print "service_messages", service_messages

            service_messages_lock.release()


# The thread which receives messages from multicasts
def listen_from_multicast():

    global total_grp_sockets

    while (True):

        buffers_lock.acquire()
        current_grp_sockets = total_grp_sockets
        buffers_lock.release()

        ready, _, _ = select.select(current_grp_sockets, [], [], 1)

        for grp_socket in ready:

            print grp_socket ,"is ready"

            packet, addr = grp_socket.recvfrom(1024)
            name, message, seq_num = deconstruct_packet(MESSAGE_ENCODING, packet)

            name = name.strip('\0')
            message = message.strip('\0')

            buffers_lock.acquire()

            # Get group info
            grp_ipaddr = grp_sockets_grp_info[grp_socket][0]
            grp_port = grp_sockets_grp_info[grp_socket][1]
            # Update sequence number
            last_received_seq_number[(grp_ipaddr, grp_port)] = max(last_received_seq_number[(grp_ipaddr, grp_port)], seq_num)


            buffers_lock.release()

            # Update recv_messages
            recv_messages_lock.acquire()
            recv_messages[(grp_ipaddr, grp_port)][seq_num] = name + ": " + message
            print "Got message", recv_messages
            recv_messages_lock.release()


# The thread which sends the messages to the mmulticasts
def send_to_multicast():

    while (True):

        send_messages_lock.acquire()

        # For each group
        for grp_pair in send_messages.keys():

            buffers_lock.acquire()
            grp_socket = grp_info_grp_sockets[grp_pair]
            name = grp_info_my_name[grp_pair]
            buffers_lock.release()

            # Send all the messages and delete them !!!!!(tha allaksei)
            for i in xrange(len(send_messages[grp_pair])):

                buffers_lock.acquire()
                last_received_seq_number[grp_pair] += 1
                packet = construct_message_packet(name, send_messages[grp_pair][i], last_received_seq_number[grp_pair])
                buffers_lock.release()

                print "Send message to", grp_pair

                grp_socket.sendto(packet, grp_pair)

            send_messages[grp_pair] = []

        send_messages_lock.release()

        time.sleep(0.05)

# ............................. </THREADS> ............................. #
