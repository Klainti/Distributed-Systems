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

sock_max_reqid = {}
sock_max_reqid_lock = thread.allocate_lock()
##################/Sender/#####################

reply_buffer = {}
reply_buffer_lock = thread.allocate_lock()

reqid_to_sock_buffer = {}
reqid_to_sock_lock = thread.allocate_lock()


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
        #print 'Register: %s' % service_buffer
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
    #print 'Befoce deletion of {} service: {} and {}'.format(svcid,connection_buffer,connection_list)
    #print 'Before unregister, request buffer: {}'.format(request_buffer)

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

    #print 'After deletion of {} service, request buffer: {}'.format(svcid,request_buffer)
    request_buffer_lock.release()


    #print 'After deletion of {} service: {} and {}'.format(svcid,connection_buffer,connection_list)
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

    #print 'Add a client: %s' % connection_buffer
    connection_buffer_lock.release()


# initialize max_reqid for a new connection
def init_max_reqid(sock):

    sock_max_reqid_lock.acquire()
    sock_max_reqid[sock] = 0
    #print 'Maxreq id for each sock: %s' % sock_max_reqid
    sock_max_reqid_lock.release()

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

    #print 'Remove a client: %s' % connection_buffer
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
        print 'Unsupported service for {} request'.format(sock)
        service_buffer_lock.release()
        return None
    service_buffer_lock.release()

    request_buffer_lock.acquire()

    if (svcid not in request_buffer.keys()):
        request_buffer[svcid] = [(sock,data,reqid)]
    else:
        request_buffer[svcid].append((sock,data,reqid))

    print 'Add a request: %s' %request_buffer
    request_buffer_lock.release()

def get_sock_from_requests(svcid):

    request_buffer_lock.acquire()

    if (svcid in request_buffer.keys()):
        if (request_buffer[svcid]==[]):
            request_buffer_lock.release()
            return None
        else:
            request = request_buffer[svcid][0]

            #print 'Get a request: {}'.format(request)
            #update request buffer
            del request_buffer[svcid]
            #print 'Update request_buffer: %s' % request_buffer

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
    #print 'Add a reply: %s' % reply_buffer
    reply_buffer_lock.release()
    return 1


def establish_connection(client_ip,client_port):

    #Create the TCP socket
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_socket.settimeout(TIMEOUT)

    try:
        #print 'Try connecting to IP: %s, port: %d' %(client_ip,client_port)
        tcp_socket.connect((client_ip,client_port))


        #Check if connection establish!
        try:
            msg = tcp_socket.recv(5)
            #print 'Server: %s connected to : %s' % (tcp_socket.getsockname(),tcp_socket.getpeername())
            #print 'Connection complete'
            return tcp_socket
        except socket.error:
            #print "Connection failed. Try again!"
            tcp_socket.close()
            return None

    except socket.timeout:
        #print 'Timeout!! Try again to connect!'
        return establish_connection(client_ip,client_port)
    except socket.error:
        #print "Connection failed. Try again!"
        tcp_socket.close()
        return None

#Receive from multicast and tries to connect with a client
def search_for_clients():

    udp_socket = socket_for_multicast()

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
                    remove_client(sock)
                else:
                    data, reqid = deconstruct_packet(DECODING,packet)
                    print ("Reqid: {} at time: {}").format(reqid,time.time())
                    
                    #check for duplicate request for this sock
                    new_request = True
                    sock_max_reqid_lock.acquire()
                    if (sock_max_reqid[sock]>= reqid):
                        print 'Request {} has served in the past'.format(reqid)
                        new_request = False
                    else:
                        # update max_reqid for this sock
                        sock_max_reqid[sock] += 1
                        #print 'Maxreqid for each sock: %s' % sock_max_reqid
                    sock_max_reqid_lock.release()
                        
                    if (new_request):
                
                        svcid = map_sock_to_service(sock)
                    
                        if (svcid != None):
                            add_request(svcid,sock,data.rstrip('\0'),reqid)
                            #print 'Received data: %s' % data.rstrip('\0')
                        else:
                            'Unsupported service'

def send_to_clients_thread():

    while (1):

        reply_buffer_lock.acquire()
        tmp_reply_buffer = reply_buffer
        reply_buffer_lock.release()

        # Send replies!!
        for key in tmp_reply_buffer.keys():
            sock,data,client_reqid = tmp_reply_buffer[key]
            print "Send reqid:{} , time: {}".format(client_reqid,time.time())

            packet = construct_packet(DECODING,data,client_reqid)
            if (len(packet) == sock.send(packet)):
                #update reply buffer!
                reply_buffer_lock.acquire()
                #print 'Reply buffer: %s' % reply_buffer
                del reply_buffer[key]
                #print 'Send a reply: %s' % reply_buffer
                reply_buffer_lock.release()

def reqid_generator():

    global my_reqid
    my_reqid += 1
    
    return my_reqid 


# Return a reqid from reqid_to_sock_buffer
def getRequest (svcid,buf,length):

    tmp_tuple = get_sock_from_requests(svcid)

    # failed to get a request!
    if (tmp_tuple == None):
        return -1

    sock = tmp_tuple[0]
    buf = tmp_tuple[1]
    client_reqid = tmp_tuple[2]
    server_reqid = reqid_generator()

    # Map reqid to sock for reply !
    if (not map_reqid_to_sock(server_reqid,sock,client_reqid)):
        return -1

    return server_reqid

# Send a reply to a client
def sendReply(server_reqid,buf,length):
    
    reqid_to_sock_lock.acquire()

    # check reqid has sock 
    if (server_reqid not in reqid_to_sock_buffer.keys()):
        reqid_to_sock_lock.release()
        return -1

    sock, client_reqid = reqid_to_sock_buffer[server_reqid]

    #update buffer
    #print 'Map reqid to sock: {}'.format(sock)
    del reqid_to_sock_buffer[server_reqid]
    #print 'Update reqid_to_sock_buffer: %s' % reqid_to_sock_buffer

    reqid_to_sock_lock.release()

    if (add_reply(server_reqid,sock,buf,client_reqid)):
        return -1

    return 1


# Spawn sender/receiver threads!
def init():

    #Spawn a thread to search for clients and to establish connection!
    thread.start_new_thread(search_for_clients,())

    #Spawn a thread to receive requests from clients
    thread.start_new_thread(receive_from_clients_thread,())

    #Spawn a thread to send replies to clients
    thread.start_new_thread(send_to_clients_thread,())
