import socket
from packet_struct import *

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_port = tcp_socket.getsockname()[1]

service_ip = raw_input("Give service IP: ")
service_port = int(raw_input("Give service port: "))
service_addr = (service_ip, service_port)

tcp_socket.connect(service_addr)

grp_ip = raw_input("Give group chat IP: ")
grp_port = int(raw_input("Give group chat port: "))
nickname = raw_input("Give nickname: ")
request_for_grp = construct_join_packet(grp_ip, grp_port, nickname)

tcp_socket.send(request_for_grp)

while (1):
    reply = tcp_socket.recv(1024)

    name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, reply)
    name.strip('\0')

    if (state == 1):
        print name, "is connected"
    elif (state == -1):
        print name, "is disconnected"

    exit = raw_input("Exit?[0/1] ")

    if (exit == "1"):
        tcp_socket.send ("Bye")
        break

reply = tcp_socket.recv(1024)

name, state = deconstruct_packet(MEMBER_CONN_DIS_ENCODING, reply)
name.strip('\0')

if (state == 1):
    print name, "is connected"
elif (state == -1):
    print name, "is disconnected"
