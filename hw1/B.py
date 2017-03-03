import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket
from netfifo import *
##testing !
fd = netfifo_rcv_open(10000,10)
print netfifo_read(fd,1024)
netfifo_rcv_close(fd)
