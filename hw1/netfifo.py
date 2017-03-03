"""
    API for FIFO pipe with UDP/IP connection
"""

import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket
import struct

#Globals variables!
fd_list = []
buffer_size = 0


#create a packet ACK or Data
"""
    encode: ! -> network( = big endian)
            h -> short integer
            q -> long long integer
            s -> string
"""

def construct_packet(ack_or_data,number_of_packet,payload):
    
    return struct.pack('!hq10s', ack_or_data,number_of_packet,payload)

#deconstruct packet
def deconstruct_packet(packet):

    return struct.unpack('!hq10s',packet)

#Open reading side of pipe. Return a positive integer as file discriptor 
def netfifo_rcv_open(port,bufsize):

    #initial buffer
    global buffer_size
    buffer_size = bufsize

    #create Server object (reading side)
    socket_object = SocketServer(socket.AF_INET,socket.SOCK_DGRAM,Hostname(),port,1)

    fd_list.append(socket_object)

    return fd_list.index(socket_object)
    
#reading from pipe. Return data.
def netfifo_read(fd,size):
    
    sock = fd_list[fd]

    #read data and unpack
    data = deconstruct_packet(sock.ReceiveFrom(size)[0])

    #data[0] = ack or data,data[1] = number of packet,data[2] = payload
    #check the packet, payload = 1
    if (data[0]==1):
        return data[2]
    else:
        return (data[1])


#close reading side
def netfifo_rcv_close(fd):

    sock = fd_list[fd]

    sock.Close()

#Open writing side of pipe. Return a positive integer as file discriptor
def netfifo_snd_open(host,port,bufsize):

    #initial buffer
    global buffer_size
    buffer_size = bufsize

    #create Server object (writing side)
    socket_object = SocketClient(socket.AF_INET,socket.SOCK_DGRAM,1)
    socket_object.Connect(host,port)

    fd_list.append(socket_object)

    return fd_list.index(socket_object)

#writing data in pipe
def netfifo_write(fd,buf,size):

    sock = fd_list[fd]

    packet = construct_packet(1,1,buf)

    sock.Send(packet)

#close writing side
def netfifo_snd_close(fd):

    sock = fd_list[fd]

    sock.Close()

