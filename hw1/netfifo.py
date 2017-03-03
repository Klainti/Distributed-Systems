"""
    API for FIFO pipe with UDP/IP connection
"""

PACKET_SIZE = 20

import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket
import struct

import thread
import threading

fd_list = []
rcv_buffer_size = 0
#buffer (dictionary [key: payload])
rcv_buf = {}

################################# RCV ################################# 
#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
rcv_app_wait_mtx = threading.Lock()
rcv_app_wait_mtx.acquire()
rcv_app_wait = 0

#mutex for sychronization between thread and app
rcv_thread_app_mtx = threading.Lock()

#next packet app wants to read from buffer (starts from 1)
rcv_next_app_read = 1
#next packet thread wants to read from socket (starts from 1)
rcv_next_waiting = 1
#number of packets in buffer
rcv_in_buffer = 0
################################# RCV #################################



################################# SEND ################################# 
#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
snd_app_wait_mtx = threading.Lock()
snd_app_wait_mtx.acquire()
snd_app_wait = 0

#mutex for sychronization between thread and app
snd_thread_app_mtx = threading.Lock()

#next packet app wants to read from buffer (starts from 1)
snd_next_app_read = 1
#next packet thread wants to read from socket (starts from 1)
snd_next_waiting = 1
#number of packets in buffer
snd_in_buffer = 0
################################# SEND #################################





#thread code
def rcv_thread (sock):
	
	global rcv_next_waiting
	global rcv_next_app_read
	global rcv_in_buffer
	global rcv_buffer_size
	
	while (True):
		
		unlock = True
		
		print "Thread waits"
		
		
		#wait for next packet
		data = deconstruct_packet(sock.ReceiveFrom(PACKET_SIZE)[0])
		
		
		print "Thread:", data
		
		rcv_thread_app_mtx.acquire()
		
		
		print data[1], rcv_next_waiting, rcv_in_buffer, rcv_buffer_size
		
		#if it isnt the next packet or buffer is full throw it 
		#else update buffer
		if (data[1] == rcv_next_waiting and rcv_in_buffer < rcv_buffer_size):
			rcv_buf.update( {rcv_next_waiting: data[2]} )
			rcv_next_waiting += 1
			rcv_in_buffer += 1
			print "Thread: Received packet" ,data[1] , rcv_in_buffer, "/", rcv_buffer_size
		
		
			#if app waits give it priority
			if (rcv_app_wait and rcv_next_app_read < rcv_next_waiting):
				rcv_app_wait_mtx.release()
				unlock = False
				
		if (unlock):
			rcv_thread_app_mtx.release()










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
    global rcv_buffer_size
    rcv_buffer_size = bufsize

    #create Server object (reading side)
    socket_object = SocketServer(socket.AF_INET,socket.SOCK_DGRAM,Hostname(),port,0)

    #start the thread
    thread.start_new_thread (rcv_thread, (socket_object, ))

    fd_list.append(socket_object)



    return fd_list.index(socket_object)
    
#reading from pipe. Return data.
def netfifo_read(fd,size):
    
    global rcv_next_app_read
    global rcv_app_wait
    global rcv_in_buffer
    
    
    #app wants to read packet next_app_read
    rcv_thread_app_mtx.acquire()
    if (rcv_next_app_read not in rcv_buf):
		#if packet not in buf wait
		print "App waits for packet " ,rcv_next_app_read
		rcv_app_wait = 1
		rcv_thread_app_mtx.release()
		rcv_app_wait_mtx.acquire()
		rcv_app_wait = 0

	
    d = rcv_buf[rcv_next_app_read]
    rcv_next_app_read += 1
    rcv_in_buffer -= 1
    del rcv_buf[rcv_next_app_read-1]
    print "App got packet", rcv_next_app_read-1
    
    rcv_thread_app_mtx.release()

    return d


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

