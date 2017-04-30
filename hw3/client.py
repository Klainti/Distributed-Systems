import socket
from packet_struct import *
from msglib import *

service_ip = raw_input("Give service IP: ")
service_port = int(raw_input("Give service port: "))

# set Directory service address!
grp_setDir(service_ip, service_port)

#grp_ip = raw_input("Give grp chat IP: ")
#grp_port = int(raw_input("Give grp port: "))
#nickname = raw_input("Give nickname: ")

# Join to a group
gsocket1 = grp_join("224.29.3.1", 10000, "takis")
gsocket2 = grp_join("224.29.3.2", 15000, "takis")
"""
while (1):

    send_receive = int(raw_input("Send or Receive (0/1): "))
    if (send_receive == 0):
        gsocket.sendto('Hello', (grp_ip, grp_port))
    elif (send_receive == 1):
        print gsocket.recvfrom(1024)
    else:
        grp_leave(gsocket)
        break
"""
while (True):
    pass
