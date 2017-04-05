import socket
import struct
import sys
import thread
import time
import select
import os
from packet_struct import *

########################## <CUSTOM ERRORS> ##########################
class TakenError(Exception):
   def __init__(self, value):
       self.value = value
   def __str__(self):
       return repr(self.value)

class MissingReply(Exception):
   def __init__(self, value):
       self.value = value
   def __str__(self):
       return repr(self.value)
########################## </CUSTOM ERRORS> ##########################


########################## <COSTANTS> ##########################
MULTI_IP = ''
MULTI_PORT = 0
MY_IP = ''

TIMEOUT = 0.5
########################## </COSTANTS> ##########################


########################## <VARIABLES> ##########################
svcid_sock = {}
svcid_sock_lock = thread.allocate_lock()

sock_svcid = {}
sock_svcid_lock = thread.allocate_lock()

new_requests = {}
new_requests_lock = thread.allocate_lock()

replies = {}
replies_lock = thread.allocate_lock()

sock_requests = {}
sock_requests_lock = thread.allocate_lock()

sock_time = {}
sock_time_lock = thread.allocate_lock()

total_sockets = []
total_sockets_lock = thread.allocate_lock()

reqid_svcid = {}
reqid_svcid_lock = thread.allocate_lock()

taken_reqids = []


mtx = thread.allocate_lock()


next_reqid = 0

next_server = 0

waiting_reqid = -1
getReply_lock = thread.allocate_lock()
getReply_lock.acquire()

end_of_proccess = False
end_of_proccess_lock = thread.allocate_lock()

send_data_exit = thread.allocate_lock()
send_data_exit.acquire()

receive_data_exit = thread.allocate_lock()
receive_data_exit.acquire()
########################## </VARIABLES> ##########################


########################## <INIT> ##########################
def init():

    global MY_IP

    thread.start_new_thread(send_data,())
    thread.start_new_thread(receive_data,())

    s1 = os.popen('/sbin/ifconfig wlan0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    s2 = os.popen('/sbin/ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    if (len(s1)>16 or len(s1) < 7):
        MY_IP = s2
    else:
        MY_IP = s1

    print "MY_IP:", MY_IP
########################## </INIT> ##########################

########################## <THREADS' FUNCTIONS> ##########################
#Find connected servers for svcid
def find_connected_servers (svcid):


    svcid_sock_lock.acquire()

    if (svcid in svcid_sock.keys()):
        tmp_list = svcid_sock[svcid]
    else:
        tmp_list = []

    svcid_sock_lock.release()

    return tmp_list


def sock_requests_add (sock, reqid):

    sock_requests_lock.acquire()
    if (sock_requests.has_key(sock)):
        sock_requests[sock].append(reqid)
    else:
        sock_requests[sock] = [reqid]
    sock_requests_lock.release()


def check_for_unactive_sockets():

    print "*****\nCheck for unactive servers"

    mtx.acquire()

    sock_time_lock.acquire()

    for s in sock_time.keys():

        if (time.clock() - sock_time[s] > 20*TIMEOUT):

            print "Socket:", s, "offline"

            sock_requests_lock.acquire()

            for r in sock_requests[s]:

                reqid_svcid_lock.acquire()
                svcid = reqid_svcid[r]
                reqid_svcid_lock.release()

                new_requests_lock.acquire()

                pos = 0
                while (pos < len(new_requests[svcid])):
                    if (new_requests[svcid][pos][1] == r):
                        new_requests[svcid][pos][2] = False
                        break
                    pos += 1

                new_requests_lock.release()

            del sock_requests[s]

            sock_requests_lock.release()


            del sock_time[s]

            total_sockets_lock.acquire()
            total_sockets.remove(s)
            total_sockets_lock.release()

            sock_svcid_lock.acquire()
            svcid = sock_svcid[s]
            del sock_svcid[s]
            sock_svcid_lock.release()

            svcid_sock_lock.acquire()
            svcid_sock[svcid].remove(s)
            svcid_sock_lock.release()

            s.close()

    print "Check for unactive servers done\n*****"

    sock_time_lock.release()

    mtx.release()

# Add a server to the svcid_sock
def add_server(svcid,socket):

    svcid_sock_lock.acquire()

    # check service already has at least one server!
    if (svcid in svcid_sock.keys()):
        svcid_sock[svcid].append(socket)
    else:
        svcid_sock[svcid] = [socket]

    #print "Connected servers: ", svcid_sock

    svcid_sock_lock.release()

    sock_svcid_lock.acquire()
    sock_svcid[socket] = svcid
    sock_svcid_lock.release()

    total_sockets_lock.acquire()
    total_sockets.append (socket)
    total_sockets_lock.release()

#Send multicast for svcid
def send_multicast(svcid):

    multicast_group = (MULTI_IP,MULTI_PORT)

    tcp_port = 0


    #Create the datagram socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #Create TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((MY_IP, tcp_port))
    tcp_port = tcp_socket.getsockname()[1]
    tcp_socket.settimeout(TIMEOUT)

    connected_servers = 0

    try:
        #Send data to the multicast group
        #print 'Sending IP: %s and port: %d' % (MY_IP, tcp_port)
        packet = construct_broadcast_packet(BROADCAST_ENCODING, MY_IP, tcp_port, svcid)
        sent = udp_sock.sendto(packet, multicast_group)

        end_of_connections = False

        while(not end_of_connections):

            try:
                tcp_socket.listen(1)
                conn, addr = tcp_socket.accept()
                conn.send('Hello')

                add_server(svcid,conn)

                connected_servers += 1

                #print 'Connected at: %s' % str(addr)
            except socket.timeout:
                end_of_connections = True
                #print 'Time out, no more connections'
    finally:
        pass

    return connected_servers

    tcp_socket.close()
########################## </THREADS' FUNCTIONS> ##########################

########################## <THREADS> ##########################
def receive_data():

    global waiting_reqid
    global next_server

    while (1):

        end_of_proccess_lock.acquire()
        if (end_of_proccess):
            end_of_proccess_lock.release()
            break
        end_of_proccess_lock.release()

        ready,_,disconnected = select.select (total_sockets, [], [], TIMEOUT)

        #Receive replies for ready sockets
        for sock in ready:

            try:
                packet = sock.recv (1024)
            except socket.error:
                disconnected.append (sock)
                continue

            #If a socket sends empy packet means it went offline
            if (packet == ""):
                disconnected.append (sock)
                continue


            data, reqid = deconstruct_packet (REQ_ENCODING, packet)

            #Delete the request from the dictionary new_requests
            reqid_svcid_lock.acquire()
            svcid = reqid_svcid[reqid]
            reqid_svcid_lock.release()

            new_requests_lock.acquire()

            pos = 0
            while (pos < len(new_requests[svcid])):
                if (new_requests[svcid][pos][1] == reqid):
                    del new_requests[svcid][pos]
                    break
                pos += 1

            new_requests_lock.release()

            #print "Received packet with reqid:", reqid


            #Add reply to dictionary replies
            replies_lock.acquire()
            replies[reqid] = data
            if (waiting_reqid == reqid):
                getReply_lock.release()
            replies_lock.release()

            #Remove request from dictionary sock_requests
            sock_requests_lock.acquire()

            try:
                sock_requests[sock].remove(reqid)
            except:
                print reqid
                pass
            #print "Remaining socket requests:", sock_requests

            sock_requests_lock.release()

        #The part of deleting a socket mustn't execute together with send_data
        mtx.acquire()

        for sock in disconnected:


            print "Socket:", sock, "offline"

            sock_requests_lock.acquire()

            #Every request send to the disconnected socket must be send again
            for r in sock_requests[sock]:

                reqid_svcid_lock.acquire()
                svcid = reqid_svcid[r]
                reqid_svcid_lock.release()

                new_requests_lock.acquire()

                pos = 0
                while (pos < len(new_requests[svcid])):
                    if (new_requests[svcid][pos][1] == r):
                        new_requests[svcid][pos][2] = False
                        break
                    pos += 1

                new_requests_lock.release()

            del sock_requests[sock]

            sock_requests_lock.release()

            #Remove socket from every buffer
            total_sockets_lock.acquire()
            total_sockets.remove(sock)
            total_sockets_lock.release()

            next_server = max(0, next_server -1)

            sock_svcid_lock.acquire()
            svcid = sock_svcid[sock]
            del sock_svcid[sock]
            sock_svcid_lock.release()

            svcid_sock_lock.acquire()
            svcid_sock[svcid].remove(sock)
            svcid_sock_lock.release()

            #Finally close the socket
            sock.close()

        mtx.release()

    receive_data_exit.release()

def send_data():

    global next_server

    while(1):


        end_of_proccess_lock.acquire()
        if (end_of_proccess):
            end_of_proccess_lock.release()
            break
        end_of_proccess_lock.release()


        mtx.acquire()

        #Ready to send the new requests
        new_requests_lock.acquire()
        tmp_requests = new_requests
        new_requests_lock.release()

        if (len(tmp_requests) > 0):


            #For each family of service id in the requests find the servers family (tmp_list)
            for svcid in tmp_requests.keys():

                if (tmp_requests[svcid] == []):
                    continue

                tmp_servers = find_connected_servers(svcid)

                #For each request with this service id
                #Round-Robin servers
                if (len(tmp_servers) > 0):

                    for req in tmp_requests[svcid]:

                        if (req[2] == False):

                            req[2] = True

                            sock_requests_add (tmp_servers[next_server], req[1])

                            #print "Sending packet with service id:", req[1]
                            packet = construct_packet(REQ_ENCODING, req[0], req[1])
                            try:
                                tmp_servers[next_server].send(packet)
                            except socket.error:
                                continue
                            #print "Time: {}".format(time.time())



                            next_server = (next_server+1)%len(tmp_servers)

                else:
                    #print "No server for service:", svcid, "(send_multicast)"

                    #Find servers for svcid
                    connected_servers = send_multicast(svcid)

                    #Not a single server found (delete requests)
                    if (connected_servers == 0):
                        #print "No servers found for service:", svcid

                        new_requests_lock.acquire()
                        replies_lock.acquire()

                        for req in new_requests[svcid]:
                            replies[req[1]] = "ERROR"
                        del new_requests[svcid]

                        replies_lock.release()
                        new_requests_lock.release()

        mtx.release()

    send_data_exit.release()

########################## </THREADS> ##########################


########################## <API> ##########################

def sendRequest (svcid, data):

    global next_reqid

    reqid_svcid_lock.acquire()
    reqid_svcid[next_reqid] = svcid
    reqid_svcid_lock.release()

    new_requests_lock.acquire()

    if (new_requests.has_key(svcid)):
        new_requests[svcid].append ([data, next_reqid, False])
    else:
        new_requests[svcid] = [[data, next_reqid, False]]

    #print "*****\nAdd request with reqid:", next_reqid, "\n*****"

    next_reqid += 1

    new_requests_lock.release()

    return next_reqid-1

def getReply(reqid, timeout):

    global waiting_reqid

    if (reqid in taken_reqids):
        raise TakenError("Reply already taken")
        return

    if (timeout == 0):
        replies_lock.acquire()
        if (replies.has_key(reqid)):
            r = replies[reqid]
            del replies[reqid]
            replies_lock.release()
            taken_reqids.append(reqid)
            return r
        else:
            replies_lock.release()
            raise MissingReply("Reply not received")
            return
    elif (timeout < 0):
        while (1):
            replies_lock.acquire()
            if (replies.has_key(reqid)):
                r = replies[reqid]
                del replies[reqid]
                replies_lock.release()
                taken_reqids.append(reqid)
                return r
            waiting_reqid = reqid
            replies_lock.release()
            getReply_lock.acquire()
            waiting_reqid = -1
    else:
        stime = time.clock()
        while (time.clock()-stime < timeout):
            replies_lock.acquire()
            if (replies.has_key(reqid)):
                r = replies[reqid]
                del replies[reqid]
                replies_lock.release()
                taken_reqids.append (reqid)
                return r
            replies_lock.release()
            time.sleep(0.001)
        return "ERROR"

def setDiscoveryMulticast (multi_ip, port):

    global MULTI_IP
    global MULTI_PORT

    MULTI_IP = multi_ip
    MULTI_PORT = port

    init()

def close () :

    end_of_proccess_lock.acquire()
    end_of_proccess = True
    end_of_proccess_lock.release()

    send_data_exit.acquire()
    receive_data_exit.acquire()

    total_sockets_lock.acquire()
    for s in total_sockets:
        s.close()
    total_sockets = []
    total_sockets_lock.release()




########################## </API> ##########################
