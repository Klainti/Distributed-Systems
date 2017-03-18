import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time

file_name = raw_input('File name: ')
output_fd = open(file_name,'w')

port = 0
fd = netfifo_rcv_open(port,50000)

s = netfifo_read(fd,10000000)

output_fd.write(s)

output_fd.close()

time.sleep (3)

netfifo_rcv_close(fd)
