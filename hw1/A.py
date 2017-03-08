from netfifo import *
import sys
from struct import *
import time
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket

host = 'ThinkPad-Edge-E540'
port = 10000

#input
input_fd = open('file.txt','r')


fd = netfifo_snd_open(Hostname(),port,10)

for line in input_fd:
    netfifo_write(fd,line,len(line))

#netfifo_write(fd,"hello world",11)

while(1):
    pass

netfifo_snd_close(fd)
