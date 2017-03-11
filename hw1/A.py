from netfifo import *
import sys
from struct import *
import time
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket

host = '127.0.1.1'
port = 10000

#input
input_fd = open('file.txt','r')


fd = netfifo_snd_open(host,port,10)

for line in input_fd:	
	try:    
		netfifo_write(fd,line,len(line))	
	except ReceiverError:
		print "netfifo_write failed"
		break

input_fd.close()

netfifo_snd_close(fd)

input_fd = open('file.txt','r')


fd = netfifo_snd_open(host,port,10)

for line in input_fd:	
	try:    
		netfifo_write(fd,line,len(line))	
	except ReceiverError:
		print "netfifo_write failed"
		break

input_fd.close()

#netfifo_write(fd,"hello",5)
#netfifo_write(fd,"hello",5)
#netfifo_write(fd,"hello",5)
#netfifo_write(fd,"hello",5)
#netfifo_write(fd,"heo",3)

netfifo_snd_close(fd)
