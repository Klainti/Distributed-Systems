from netfifo import *
import sys
from struct import *
import time
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket

host = raw_input('host\'s IP: ')
port = int(raw_input('host\'s port: '))


file_list = ['file10k.txt','file100k.txt','file1000k.txt','file10000k.txt']
#fd = netfifo_snd_open(host,port,50000)

for item in file_list:
    input_fd = open(item,'r')
    
    print item
    #open write pipe
    fd = netfifo_snd_open(host,port,50000)

    data = input_fd.read()

    try:
    	netfifo_write(fd,data,len(data))
    except ReceiverError:
	    print "Cant reach Reicever"
    
    input_fd.close()

    netfifo_snd_close(fd)

#netfifo_snd_close(fd)
