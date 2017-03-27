import socket
import struct
import sys
import thread
import time
from packet_struct import *


MULTI_IP = '224.3.29.71'
MULTI_PORT = 10000




TIMEOUT = 0.2

server_list = {}
server_list_lock = thread.allocate_lock()

new_requests = {}
new_requests_lock = thread.allocate_lock()

next_reqid = 0


def send_data():

    while(1):


        #Ready to send the new requests
        new_requests_lock.acquire()
        tmp_requests = new_requests
        new_requests_lock.release()



        if (len(tmp_requests) > 0):

            #print "Current Requests:", tmp_requests

            #For each family of service id in the requests find the servers family (tmp_list)
            for svcid in tmp_requests.keys():

                server_list_lock.acquire()
                if (svcid in server_list.keys()):
                    tmp_list = server_list[svcid]
                else:
                    tmp_list = []
                server_list_lock.release()

                pos = 0
                #For each request with this service id
                #Round-Robin servers
                if (len(tmp_list) > 0):
                    for req in tmp_requests[svcid]:
                        print "Sending packet with service id:", req[1]
                        packet = construct_packet(REQ_ENCODING, req[0], req[1])
                        tmp_list[pos].send(packet)
                        pos = (pos+1)%len(tmp_list)

                    new_requests_lock.acquire()
                    del new_requests[svcid]
                    new_requests_lock.release()

                else:
                    print "Cant send request with service id:", svcid

# Add a server to t server_list
def add_server(svcid,socket):

    server_list_lock.acquire()

    # check service already has at least one server!
    if (svcid in server_list.keys()):
        server_list[svcid].append(socket)
    else:
        server_list[svcid] = [socket]

    print "Connected servers: ", server_list

    server_list_lock.release()

def set_discover_multicast(ipaddr,port,svcid):

    multicast_group = (MULTI_IP,MULTI_PORT)

    #Create the datagram socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #Create TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((ipaddr,port))
    port = tcp_socket.getsockname()[1]
    tcp_socket.settimeout(TIMEOUT)

    server_connection = False
    while(not server_connection):

        try:
            #Send data to the multicast group
            print 'Sending IP: %s and port: %d' % (ipaddr,port)
            packet = construct_broadcast_packet(BROADCAST_ENCODING,ipaddr,port,svcid)
            sent = udp_sock.sendto(packet,multicast_group)

            try:
                tcp_socket.listen(1)
                conn, addr = tcp_socket.accept()
                conn.send('Hello')

                add_server(svcid,conn)

                print 'Connected at: %s' % str(addr)
                server_connection = True
            except socket.timeout:
                print 'Time out, no connection occur'
        finally:
            pass

def sendRequest (svcid, data):

    global next_reqid

    new_requests_lock.acquire()

    if (new_requests.has_key(svcid)):
        new_requests[svcid].append ([data, next_reqid])
    else:
        new_requests[svcid] = [[data, next_reqid]]

    print "Add request with reqid:", next_reqid
    print "Requests buffer:", new_requests

    next_reqid += 1

    new_requests_lock.release()



def setDiscoveryMulticast (ip, port, svcid):

    set_discover_multicast(ip, port, svcid)
    thread.start_new_thread(send_data,())
