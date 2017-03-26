import socket
from packet_struct import *
from multicast_module import *

def establish_connection(client_addr):

    #Create the TCP socket
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_socket.settimeout(TIMEOUT)

    try:
        print 'Try connecting to IP: %s, port: %d' %(client_addr[0],client_addr[1])
	tcp_socket.connect(client_addr)


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
        return establish_connection(client_addr)


#Receive from multicast and tries to connect with a client
def search_for_clients():

    udp_socket = socket_for_multicast()

    # Try to connect with a client
    while (1):

        # wait for a client
        client_addr = receive_from_multicast(udp_socket)

        tcp_socket = establish_connection(client_addr)

search_for_clients()
