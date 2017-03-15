from netfifo import *
import sys
from struct import *
import time
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket

host = raw_input('host\'s IP: ')
port = 10000

#input
input_fd = open('file.txt','r')


fd = netfifo_snd_open(host,port,50000)

data = input_fd.read()

try:
	netfifo_write(fd,data,len(data))
except ReceiverError:
	print "Cant reach Reicever"


input_fd.close()

netfifo_snd_close(fd)
