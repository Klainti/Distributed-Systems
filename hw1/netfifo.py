"""
    API for FIFO pipe with UDP/IP connection
"""

import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket
import struct

import thread
import threading

#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
app_wait_mtx = threading.Lock()
app_wait_mtx.acquire()
app_wait = 0

#mutex for sychronization between thread and app
thread_app_mtx = threading.Lock()

#next packet app wants to read from buffer (starts from 1)
next_app_read = 1
#next packet thread wants to read from socket (starts from 1)
next_waiting = 1
#number of packets in buffer
in_buffer = 0
#buffer (dictionary [key: payload])
buf = {}


#thread code
def rcv_thread (sock):
	
	global next_waiting
	global next_app_read
	global in_buffer
	global buffer_size
	
	while (True):
		
		unlock = True
		
		
		print "Thread waits"
		
		
		#wait for next packet
		data = deconstruct_packet(sock.ReceiveFrom(20)[0])
		
		
		print "Thread:", data
		
		thread_app_mtx.acquire()
		
		
		#if it isnt the next packet or buffer is full throw it 
		#else update buffer
		if (data[1] == next_waiting and in_buffer < buffer_size):
			buf.update( {next_waiting: data[2]} )
			next_waiting += 1
			in_buffer += 1
			print "Thread: Received packet" ,data[1] , in_buffer, "/", buffer_size
		
		
			#if app waits give it priority
			if (app_wait and next_app_read < next_waiting):
				app_wait_mtx.release()
				unlock = False
				
		if (unlock):
			thread_app_mtx.release()





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

    #start the thread
    thread.start_new_thread (rcv_thread, (socket_object, ))

    fd_list.append(socket_object)



    return fd_list.index(socket_object)
    
#reading from pipe. Return data.
def netfifo_read(fd,size):
    
    global next_app_read
    global app_wait
    global in_buffer
    
    
    #app wants to read packet next_app_read
    thread_app_mtx.acquire()
    if (next_app_read not in buf):
		#if packet not in buf wait
		print "App waits for packet " ,next_app_read
		app_wait = 1
		thread_app_mtx.release()
		app_wait_mtx.acquire()
		app_wait = 0

    d = buf[next_app_read]
    next_app_read += 1
    in_buffer -= 1
    
    thread_app_mtx.release()

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

