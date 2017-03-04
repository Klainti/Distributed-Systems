import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket
from netfifo import *
##testing !
port = 10000
fd = netfifo_rcv_open(port,3)
for _ in range(0,5):
    print netfifo_read(fd,1024)

netfifo_rcv_close(fd)
