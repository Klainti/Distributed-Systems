"""
    API for FIFO pipe with UDP/IP connection
"""

import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket

#Globals variables!
fd_list = []
buffer_size = 0

#Open reading side of pipe. Return a positive integer as file discriptor 
def netfifo_rcv_open(port,bufsize):

    #initial buffer
    global buffer_size
    buffer_size = bufsize

    #create Server object (reading side)
    socket_object = SocketServer(socket.AF_INET,socket.SOCK_DGRAM,Hostname(),port,1)

    fd_list.append(socket_object)

    return fd_list.index(socket_object)
    
#reading from fifo. Return data.
def netfifo_read(fd,size):
    
    sock = fd_list[fd]

    #read data
    return sock.ReceiveFrom(size)[0]


#close reading side
def netfifo_rcv_close(fd):

    sock = fd_list[fd]

    sock.Close()

##testing !
fd = netfifo_rcv_open(10000,10)
print netfifo_read(fd,1024)
netfifo_rcv_close(fd)
