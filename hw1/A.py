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

fd = netfifo_snd_open(Hostname(),port,10)
netfifo_write(fd,"Hello World",11)
netfifo_write(fd,"Hello World",11)

time.sleep (10)
netfifo_snd_close(fd)

