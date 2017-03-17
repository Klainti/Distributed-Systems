import socket
from MySocket_library import *

my_object_socket = SocketClient(socket.AF_INET,socket.SOCK_DGRAM,1)

while 1:

    data = str(raw_input())
    my_object_socket.SendTo(data,Hostname(),10000)

    print my_object_socket.ReceiveFrom(1024)[0]
