import socket
import thread
import time
import select
from packet_struct import *
from multicast_module import *
from sys import exit

DECODING = '!1016sq'


# includes all tcp connections with clients
# a dict to map sockets to services
connection_buffer = {}

# only sockets!
connection_list = []

connection_buffer_lock = thread.allocate_lock()


###################/Receiver/###################
request_buffer = {}

request_buffer_lock = thread.allocate_lock()

#timeout for select.select
TIMEOUT = 0.2

''' Register and Unregister a service for a server'''

service_buffer = []


#On success register(append to buffer) return 1, otherwise 0
def register(svcid):
    
    if (svcid not in service_buffer):
        service_buffer.append(svcid)
        return 1
    
    return 0 

#On success unregister(delete from buffer) return 1, otherwise 0
def unregister(svcid):

    if (svcid in service_buffer):
        service_buffer.remove(svcid)
        return 1

    return 0

# Add a client to connection buffer
def add_client(sock,svcid):

    connection_buffer_lock.acquire()

    # update connection_list
    connection_list.append(sock)
    
    # update connection_buffer
    if (svcid not in connection_buffer.keys()):
        connection_buffer[svcid] = [sock]
    else:
        connection_buffer[svcid].append(sock)

    connection_buffer_lock.release()

def remove_client(sock):
    
    connection_buffer_lock.acquire()

    sock.close()
    # update connection list
    connection_list.remove(sock)

    # update connection_buffer
    for key in connection_buffer.keys():
        if (sock in connection_buffer[key]):
            connection_buffer[key].remove(sock)
            break

    connection_buffer_lock.release()

# search in which service a sock belong!
def map_sock_to_service(sock):

    connection_buffer_lock.acquire()

    for key in connection_buffer.keys():

        if (sock in connection_buffer[key]):
            connection_buffer_lock.release()
            return key

    connection_buffer_lock.release()
    return None

# Add a request to the request buffer!
def add_request(sock, svcid):

    request_buffer_lock.acquire()

    if (svcid not in request_buffer.keys()):
        request_buffer[svcid] = [sock]
    else:
        request_buffer[svcid].append(sock)

    print request_buffer
    request_buffer_lock.release()

def get_sock_from_requests(svcid):

    request_buffer_lock.acquire()

    if (svcid in request_buffer.keys()):
        if (request_buffer[key]==[]):
            request_buffer_lock.release()
            return None
        else:
            request = request_buffer[key][0]

            #update request buffer
            del request_buffer[key][0]
        
            request_buffer_lock.release()
            return request

    request_buffer_lock.release()
    return None

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
            add_client(tcp_socket,client_demand_svc)

def receive_from_clients_thread():

    while(1):

        # take a copy of connections!
        connection_buffer_lock.acquire()
        clients = connection_list
        connection_buffer_lock.release()

        # receive over multiple sockets!
        if (len(clients)):
            readable,_,_  = select.select(clients, [], [],TIMEOUT)

            for sock in readable:
                packet, addr = sock.recvfrom(1024)
                dummy_bytes, reqid = deconstruct_packet(DECODING,packet)
                if (dummy_bytes == "" or reqid == ""):
                    print sock.getpeername(), "Unreachable"
                    remove_client(sock)
                else:
                    svcid = map_sock_to_service(sock)
                    add_request((sock,reqid),svcid)
                    print 'Received data: %s' % dummy_bytes



if (not register(1)):
    print 'Register service failed'
    exit(0)

#Spawn a thread to search for clients and to establish connection!
thread.start_new_thread(search_for_clients,())

#Spawn a thread to receive requests from clients
thread.start_new_thread(receive_from_clients_thread,())

while(1):
    pass
