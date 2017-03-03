from netfifo import *
import sys
from struct import *

#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')

from MySocket_library import *
import socket

host = 'ThinkPad-Edge-E540'
port = 10000

fd = netfifo_snd_open(Hostname(),10000,10)
netfifo_write(fd,"Hello World",10)
netfifo_snd_close(fd)

