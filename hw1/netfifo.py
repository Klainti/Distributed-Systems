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

fd_list = []


################################# RCV ################################# 
#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
rcv_app_wait_mtx = thread.allocate_lock()
rcv_app_wait_mtx.acquire()
rcv_app_wait = 0

#mutex for sychronization between thread and app
rcv_thread_app_mtx = thread.allocate_lock()

#next packet app wants to read from buffer (starts from 1)
rcv_next_app_read = 1
#next packet thread wants to read from socket (starts from 1)
rcv_next_waiting = 1
#number of packets in buffer
rcv_in_buffer = 0
#buffer (dictionary [key: payload])
rcv_buf = {}

rcv_buffer_size = 0
################################# RCV #################################



################################# SEND ################################# 
#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
snd_app_wait_mtx = thread.allocate_lock()
snd_app_wait_mtx.acquire()
snd_app_wait = 0

snd_thread_wait_mtx = thread.allocate_lock()
snd_thread_wait_mtx.acquire()
snd_thread_wait = 0

#mutex for sychronization between thread and app
snd_thread_app_mtx = thread.allocate_lock()

#next packet app wants to read from buffer (starts from 1)
snd_next_app_write = 1
#next packet thread wants to read from socket (starts from 1)
snd_next_sending = 1
#number of packets in buffer
snd_in_buffer = 0
#buffer (dictionary [key: payload])
snd_buf = {}

snd_buffer_size = 0
################################# SEND #################################





#thread code
def rcv_thread (sock):
	
	global rcv_next_waiting
	global rcv_next_app_read
	global rcv_in_buffer
	global rcv_buffer_size
	
	while (True):
		
		unlock = True
		
		print "Rcv_thread waits"
		
		
		#wait for next packet
		data = deconstruct_packet(sock.ReceiveFrom(PACKET_SIZE)[0])
		
		
		print "Rcv_thread: got", data
		
		rcv_thread_app_mtx.acquire()
		
		#if it isnt the next packet or buffer is full throw it 
		#else update buffer
		if (data[1] == rcv_next_waiting and rcv_in_buffer < rcv_buffer_size):
			rcv_buf.update( {rcv_next_waiting: data[2]} )
			rcv_next_waiting += 1
			rcv_in_buffer += 1
			print "Rcv_thread: Received packet" ,data[1] , "(in:", rcv_in_buffer, ")"
		
		
			#if app waits give it priority
			if (rcv_app_wait and rcv_next_app_read < rcv_next_waiting):
				rcv_app_wait_mtx.release()
				unlock = False
				
		if (unlock):
			rcv_thread_app_mtx.release()



def snd_thread (sock):
	
	global snd_next_sending
	global snd_in_buffer
	global snd_app_wait
	global snd_thread_wait
	
	while (True):
		
		print "Snd_thread ready"
		
		snd_thread_app_mtx.acquire()
		
		if (snd_in_buffer == 0):
			print "Snd_thread: Wait for new packet"
			snd_thread_app_mtx.release()
			snd_thread_wait = 1
			snd_thread_wait_mtx.acquire()
			snd_thread_wait = 0
	
		print "Snd_thread: Sending packet", snd_next_sending
		
		sock.Send(snd_buf[snd_next_sending])
		snd_next_sending += 1
		del snd_buf[snd_next_sending-1]
		snd_in_buffer -= 1
		
		if (snd_app_wait == 1):
			snd_app_wait_mtx.release()
		else:
			snd_thread_app_mtx.release()






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
    global snd_buffer_size
    snd_buffer_size = bufsize

    #create Server object (writing side)
    socket_object = SocketClient(socket.AF_INET,socket.SOCK_DGRAM,1)
    socket_object.Connect(host,port)

    #start the snd_thread
    thread.start_new_thread (snd_thread, (socket_object, ))

    fd_list.append(socket_object)

    return fd_list.index(socket_object)


#writing data in pipe
def netfifo_write(fd,buf,size):

    global snd_next_app_write
    global snd_in_buffer
    global snd_thread_wait
    global snd_buffer_size
    global snd_app_wait
    
    packet = construct_packet(1, snd_next_app_write, buf)
    
    snd_thread_app_mtx.acquire()
    
    print "App tries to add packet", snd_next_app_write
    
    if (snd_in_buffer == snd_buffer_size):
		print "App waits for empty position"
		snd_app_wait = 1
		snd_thread_app_mtx.release()
		snd_app_wait_mtx.acquire()


    snd_buf.update ({snd_next_app_write: packet})

    snd_next_app_write += 1
    snd_in_buffer += 1

    print "App added packet", snd_next_app_write-1,"(in:", snd_in_buffer, ")"

    if (snd_thread_wait == 1):
		snd_thread_wait_mtx.release()
    else:
		snd_thread_app_mtx.release()




#close writing side
def netfifo_snd_close(fd):

    sock = fd_list[fd]

    sock.Close()

