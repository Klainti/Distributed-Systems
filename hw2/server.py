import socket
from packet_struct import *
from multicast_module import *

#Receive from multicast and tries to connect with a client
def search_for_clients():

    udp_socket = socket_for_multicast()

    #Create the TCP socket
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_socket.settimeout(TIMEOUT)

    # Try to connect with a client
    connection_complete = False
    while (not connection_complete):

        # wait for a client
        client_addr = receive_from_multicast(udp_socket)

        try:
            print 'Try connecting to IP: %s, port: %d' %(client_addr[0],client_addr[1])
	    tcp_socket.connect(client_addr)


	    #Check if connection establish!
	    try:
	        msg = tcp_socket.recv(5)
	    except socket.error:
	        print "Connection failed. Try again!"
	        tcp_socket.close()

    	        #delete and create a new tcp socket!
    	        tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    	        tcp_socket.settimeout(TIMEOUT)
    	        continue

	    print 'Server: %s connected to : %s' % (tcp_socket.getsockname(),tcp_socket.getpeername())
	    print 'Connection complete'
	    connection_complete = True

	except socket.timeout:
	    print 'Trying again to connect!'

search_for_clients()
