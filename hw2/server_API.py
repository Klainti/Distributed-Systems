import socket
import thread
import time
import select
from packet_struct import *
from multicast_module import *
from sys import exit

MULTI_IP = ""
MULTI_PORT = 0

# includes all tcp connections with clients
# a dict to map sockets to services
connection_buffer = {}

# only sockets!
connection_list = []

connection_buffer_lock = thread.allocate_lock()


###################/Receiver/###################
request_buffer = {}

request_buffer_lock = thread.allocate_lock()

sock_received_reqids = {}
sock_received_reqids_lock = thread.allocate_lock()
##################/Sender/#####################

reply_buffer = {}
reply_buffer_lock = thread.allocate_lock()

reqid_to_sock_buffer = {}
reqid_to_sock_lock = thread.allocate_lock()

mtx = thread.allocate_lock()

my_reqid = 0

#timeout for select.select
TIMEOUT = 0.2

''' Register and Unregister a service for a server'''

service_buffer = []

service_buffer_lock = thread.allocate_lock()


#On success register(append to buffer) return 1, otherwise 0
def register(svcid):

    if (svcid not in service_buffer):
        service_buffer.append(svcid)
        return 1

    return 0

#On success unregister(delete from buffer) return 1, otherwise 0
def unregister(svcid):

    service_buffer_lock.acquire()

    if (svcid in service_buffer):
        service_buffer.remove(svcid)
        unsupport_service(svcid)
        service_buffer_lock.release()
        return 1

    service_buffer_lock.release()
    return 0

def unsupport_service(svcid):

    connection_buffer_lock.acquire()

    # Remove sockets from connnection list!
    for item in connection_buffer[svcid]:
        item.close()
        connection_list.remove(item)

    # Remove service and sockets from connection buffer
    del connection_buffer[svcid]

    # Remove requests for svcid

    request_buffer_lock.acquire()
    if (svcid in request_buffer.keys()):
        del request_buffer[svcid]

    request_buffer_lock.release()

    connection_buffer_lock.release()

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


# initialize max_reqid for a new connection
def init_max_reqid(sock):

    sock_received_reqids_lock.acquire()
    sock_received_reqids[sock] = []
    sock_received_reqids_lock.release()

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

def clean_up_received_reqids(sock):

    sock_received_reqids_lock.acquire()
    del sock_received_reqids[sock]
    sock_received_reqids_lock.release()

# search in which service a sock belong!
def map_sock_to_service(sock):

    connection_buffer_lock.acquire()

    for key in connection_buffer.keys():

        if (sock in connection_buffer[key]):
            connection_buffer_lock.release()
            return key

    connection_buffer_lock.release()
    return None

def map_reqid_to_sock(server_reqid,sock,client_reqid):

    reqid_to_sock_lock.acquire()

    if (server_reqid not in reqid_to_sock_buffer.keys()):
        reqid_to_sock_buffer[server_reqid] = (sock,client_reqid)
        reqid_to_sock_lock.release()
        return 1

    reqid_to_sock_lock.release()
    return 0

# Add a request to the request buffer!
def add_request(svcid,sock,data,reqid):

    #check scvid supported from server
    service_buffer_lock.acquire()
    if (svcid not in service_buffer):
        service_buffer_lock.release()
        return None
    service_buffer_lock.release()

    request_buffer_lock.acquire()

    if (svcid not in request_buffer.keys()):
        request_buffer[svcid] = [(sock,data,reqid)]
    else:
        request_buffer[svcid].append((sock,data,reqid))

    request_buffer_lock.release()

# Remove previous requests for a client
def clean_up_requests(sock):

    request_buffer_lock.acquire()

    for key in request_buffer.keys():
        i=0
        length = len(request_buffer[key])
        while(i<length):
            if (sock == request_buffer[key][i][0]):
                del request_buffer[key][i]
                length = len(request_buffer[key])
            else:
                i += 1

    request_buffer_lock.release()

def get_sock_from_requests(svcid):

    request_buffer_lock.acquire()

    if (svcid in request_buffer.keys()):
        if (request_buffer[svcid]==[]):
            request_buffer_lock.release()
            return None
        else:
            request = request_buffer[svcid][0]

            #update request buffer
            del request_buffer[svcid][0]

            request_buffer_lock.release()
            return request

    request_buffer_lock.release()
    return None

def add_reply(server_reqid,sock,data,client_reqid):

    reply_buffer_lock.acquire()

    if (server_reqid in reply_buffer.keys()):
        reply_buffer_lock.release()
        return 0

    reply_buffer[server_reqid] = (sock,data,client_reqid)

    reply_buffer_lock.release()
    return 1

def clean_up_replies(server_reqid,sock):

    reply_buffer_lock.acquire()

    if (sock != None):
        for key in reply_buffer.keys():
            if (sock == reply_buffer[key][0]):
                del reply_buffer[key]
    elif (server_reqid != None):
        del reply_buffer[server_reqid]

    reply_buffer_lock.release()

def establish_connection(client_ip,client_port):

    #Create the TCP socket
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_socket.settimeout(TIMEOUT)

    try:
        tcp_socket.connect((client_ip,client_port))


        #Check if connection establish!
        try:
            msg = tcp_socket.recv(5)
            return tcp_socket
        except socket.error:
            tcp_socket.close()
            return None

    except socket.timeout:
        return establish_connection(client_ip,client_port)
    except socket.error:
        tcp_socket.close()
        return None

#Receive from multicast and tries to connect with a client
def search_for_clients():

    udp_socket = socket_for_multicast(MULTI_IP,MULTI_PORT)

    # Try to connect with a client
    while (1):

        # wait for a client
        client_ip, client_port, client_demand_svc = receive_from_multicast(udp_socket)

        service_buffer_lock.acquire()
        tmp_service_buffer = service_buffer
        service_buffer_lock.release()

        #check the service which client looking for
        if (client_demand_svc in tmp_service_buffer):
            tcp_socket = establish_connection(client_ip,client_port)
        else:
            tcp_socket= None

        # Add the connection to buffer!
        if (tcp_socket is not None):
            add_client(tcp_socket,client_demand_svc)
            init_max_reqid(tcp_socket)

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
                if (len(packet) != 1024):
                    print sock.getpeername(), "Unreachable"
                    mtx.acquire()
                    remove_client(sock)
                    clean_up_requests(sock)
                    clean_up_replies(None,sock)
                    clean_up_received_reqids(sock)
                    mtx.release()
                else:
                    data, reqid = deconstruct_packet(REQ_ENCODING,packet)

                    #check for duplicate request for this sock
                    new_request = True
                    sock_received_reqids_lock.acquire()
                    if (reqid in sock_received_reqids[sock]):
                        new_request = False
                    else:
                        # update max_reqid for this sock
                        sock_received_reqids[sock].append(reqid)
                    sock_received_reqids_lock.release()

                    if (new_request):

                        svcid = map_sock_to_service(sock)

                        if (svcid != None):
                            add_request(svcid,sock,data.rstrip('\0'),reqid)
                        else:
                            'Unsupported service'

def send_to_clients_thread():

    while (1):

        mtx.acquire()
        reply_buffer_lock.acquire()
        tmp_reply_buffer = reply_buffer
        reply_buffer_lock.release()

        # Send replies!!
        for key in tmp_reply_buffer.keys():
            try:
                sock,data,client_reqid = tmp_reply_buffer[key]

                packet = construct_packet(REQ_ENCODING,data,client_reqid)
                sock.send(packet)
                clean_up_replies(key,None)
            except socket.error:
                pass
        mtx.release()

def reqid_generator():

    global my_reqid
    my_reqid += 1

    return my_reqid


# Return a reqid from reqid_to_sock_buffer
def getRequest (svcid,buf,length):

    tmp_tuple = get_sock_from_requests(svcid)
    while (tmp_tuple == None):
        time.sleep (0.001)
        tmp_tuple = get_sock_from_requests(svcid)



    sock = tmp_tuple[0]
    buf = tmp_tuple[1]
    client_reqid = tmp_tuple[2]
    server_reqid = reqid_generator()

    # Map reqid to sock for reply !
    if (not map_reqid_to_sock(server_reqid,sock,client_reqid)):
        return (-1,None)

    return (server_reqid,buf)

# Send a reply to a client
def sendReply(server_reqid,buf,length):

    reqid_to_sock_lock.acquire()

    # check reqid has sock
    if (server_reqid not in reqid_to_sock_buffer.keys()):
        reqid_to_sock_lock.release()
        return -1

    sock, client_reqid = reqid_to_sock_buffer[server_reqid]

    #update buffer
    del reqid_to_sock_buffer[server_reqid]

    reqid_to_sock_lock.release()

    if (add_reply(server_reqid,sock,buf,client_reqid)):
        return -1

    return 1

def setDiscoveryMulticast (multi_ip, port):

    global MULTI_IP
    global MULTI_PORT

    MULTI_IP = multi_ip
    MULTI_PORT = port

    init()


# Spawn sender/receiver threads!
def init():

    #Spawn a thread to search for clients and to establish connection!
    thread.start_new_thread(search_for_clients,())

    #Spawn a thread to receive requests from clients
    thread.start_new_thread(receive_from_clients_thread,())

    #Spawn a thread to send replies to clients
    thread.start_new_thread(send_to_clients_thread,())
