import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time

##testing !
port = 10000
fd = netfifo_rcv_open(port,10)

fd_output = open('output.txt','w')

s = netfifo_read(fd,1000)
fd_output.write(s)
print "************************************"
print "Returned value:", s
print "************************************"
while(1):
    pass

netfifo_rcv_close(fd)
