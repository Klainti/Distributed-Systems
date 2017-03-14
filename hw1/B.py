import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time

##testing !
port = 10000
fd = netfifo_rcv_open(port,50000)

output_fd = open('output.txt','w')

s = netfifo_read(fd,10000000)
output_fd.write(s)

output_fd.close()
print "File closed"
netfifo_rcv_close(fd)
