"""
A service that supports group chats.

Accept members and puts them in their appropriate group chat
Also, the service notifies others members that are already in a group chat
about joining/leaving of a member!
"""

import thread
import select
import socket
from packet_struct import *

MY_IP = "127.0.0.1"

lock = thread.allocate_lock()

#Connected sockets for every group
msggroup_sockets = {}

#All the connected sockets
total_sockets = []

#The group every socket belongs to
socket_msggroup = {}

#The name of every socket
socket_name = {}

def new_connections_thread():

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

        lock.acquire()

        new_member_packet = construct_member_packet(name, 1)

        if ((grpip, grpport) not in msggroup_sockets):
            # First member init the group chat
            msggroup_sockets[(grpip, grpport)] = [conn]
        else:
            # Send to everyone that the member with name is connected
            for member in msggroup_sockets[(grpip, grpport)]:
                member.send(new_member_packet)

            # Add member to dictionary
            msggroup_sockets[(grpip, grpport)].append(conn)

        # Send that it is connected to the group chat
        conn.send(new_member_packet)

        #Update total sockets and socket_msggroup
        total_sockets.append (conn)
        socket_msggroup[conn] = (grpip, grpport)
        socket_name[conn] = name

        print msggroup_sockets
        print total_sockets
        print socket_msggroup
        print socket_name

        lock.release()

def disconections_thread ():

    while (True):

        lock.acquire()
        current_sockets = total_sockets
        lock.release()

        ready, _, _ = select.select (current_sockets, [], [], 1)

        for s in ready:

            s.recv(1024)

            lock.acquire()

            group_info = socket_msggroup[s]
            name = socket_name[s]

            packet = construct_member_packet(name, -1)

            for member in msggroup_sockets[group_info]:
                if (member != s):
                    member.send (packet)

            s.send (packet)

            msggroup_sockets[group_info].remove (s)

            if (msggroup_sockets[group_info] == []):
                del msggroup_sockets[group_info]

            total_sockets.remove (s)
            del socket_msggroup[s]
            del socket_name[s]

            print msggroup_sockets
            print total_sockets
            print socket_msggroup
            print socket_name

            s.close()

            lock.release()


thread.start_new_thread (new_connections_thread, ())
thread.start_new_thread (disconections_thread, ())

while (True):
    pass
