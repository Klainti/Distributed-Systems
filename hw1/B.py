import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
from netfifo import *
import time

#Recieve 10MB
port = 10000
fd = netfifo_rcv_open(port,50000)

output_list = ['output10k.txt','output100k.txt','output1000k.txt','output10000k.txt']

for i in range(0,4):

    output_fd = open(output_list[i],'w')

    s = netfifo_read(fd,10000*(10**i))
    output_fd.write(s)

    output_fd.close()

print "File closed"
while(1):
    pass
#netfifo_rcv_close(fd)
