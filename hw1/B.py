import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time


output_fd = open('new_file.txt','w')

##testing !
port = 10000
fd = netfifo_rcv_open(port,10)

fd_output = open('output.txt','w')

s = netfifo_read(fd,1000)
fd_output.write(s)
print "************************************"
print "Returned value:", s
print "************************************"


s = netfifo_read(fd,1000)
fd_output.write(s)
print "************************************"
print "Returned value:", s
print "************************************"

output_fd.write (s)

output_fd.close()



netfifo_rcv_close(fd)
