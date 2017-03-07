import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time

##testing !
port = 10000
fd = netfifo_rcv_open(port,2)

s = netfifo_read(fd,30)
print "Returned value:", s

netfifo_rcv_close(fd)
