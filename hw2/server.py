import socket
import thread
import time
import select
from packet_struct import *
from multicast_module import *
from service import *
from sys import exit

# includes all tcp connections with clients
connection_buffer = []
connection_buffer_lock = thread.allocate_lock()


def establish_connection(client_ip,client_port):

    #Create the TCP socket
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_socket.settimeout(TIMEOUT)

    try:
        print 'Try connecting to IP: %s, port: %d' %(client_ip,client_port)
        tcp_socket.connect((client_ip,client_port))


        #Check if connection establish!
        try:
            msg = tcp_socket.recv(5)
            print 'Server: %s connected to : %s' % (tcp_socket.getsockname(),tcp_socket.getpeername())
            print 'Connection complete'
            return tcp_socket
        except socket.error:
            print "Connection failed. Try again!"
            tcp_socket.close()
            return None

    except socket.timeout:
        print 'Timeout!! Try again to connect!'
        return establish_connection(client_ip,client_port)
    except socket.error:
        print "Connection failed. Try again!"
        tcp_socket.close()
        return None

#Receive from multicast and tries to connect with a client
def search_for_clients():

    global connection_buffer

    udp_socket = socket_for_multicast()

    # Try to connect with a client
    while (1):

        # wait for a client
        client_ip, client_port, client_demand_svc = receive_from_multicast(udp_socket)

        #check the service which client looking for 
        if (client_demand_svc in service_buffer):
            tcp_socket = establish_connection(client_ip,client_port)
        else:
            tcp_socket= None

        # Add the connection to buffer!
        if (tcp_socket is not None):
            connection_buffer_lock.acquire()
            connection_buffer.append(tcp_socket)
            connection_buffer_lock.release()

# Receive packets from connections (clients)
def receive_from_clients():

    global connection_buffer

    while(1):

        # take a copy of connections!
        connection_buffer_lock.acquire()
        clients = connection_buffer
        connection_buffer_lock.release()

        # receive over multiple sockets!
        if (len(clients)):
            readable,_,_  = select.select(clients, [], [])

            for sock in readable:
                data, addr = sock.recvfrom(1024)
                if (data == ""):
                    print sock.getpeername(), "Unreachable"
                    sock.close()
                    connection_buffer_lock.acquire()
                    connection_buffer.remove(sock)
                    connection_buffer_lock.release()
                else:
                    print 'Received data: %s' % data

if (not register(1)):
    print 'Register service failed'
    exit(0)

#Spawn a thread to search for clients and to establish connection!
thread.start_new_thread(search_for_clients,())

#Spawn a thread to receive requests from clients
thread.start_new_thread(receive_from_clients,())

while(1):
    pass
