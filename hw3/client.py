import socket
from packet_struct import *
from msglib import *

service_ip = raw_input("Give service IP: ")
service_port = int(raw_input("Give service port: "))

# set Directory service address!
grp_setDir(service_ip, service_port)

grp_ip = raw_input("Give grp chat IP: ")
grp_port = int(raw_input("Give grp port: "))
nickname = raw_input("Give nickname: ")

# Join to a group
gsocket = grp_join(grp_ip, grp_port, nickname)

if (gsocket == -1):
    print 'Failed to connect'
else:
    while (1):

        send_receive = int(raw_input("Send or Receive (0/1): "))
        if (send_receive == 0):
            gsocket.sendto('Hello', (grp_ip, grp_port))
        elif (send_receive == 1):
            print gsocket.recvfrom(1024)
        else:
            grp_leave(gsocket)
            break
