"""network file system API."""

import socket
import threading

# Global variables!
SERVER_ADDR = ()
udp_socket = None

"""Initialize connection with server"""
def init_connection():

    global udp_socket
    
    # create socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # start nfs threads!

"""Set SERVER INFO"""
def mynfs_setSrv(ipaddr, port):

    global SERVER_ADDR

    # stores info for server
    SERVER_ADDR = (ipaddr, port)

    init_connection()
    return 1
