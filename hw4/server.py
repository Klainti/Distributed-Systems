"""Service support network file system."""


import socket
import os

# Global Variables
udp_socket = None

"""Initialize service"""
def init_srv():

    global udp_socket
    udp_port = 0

    s1 = os.popen('/sbin/ifconfig wlan0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    s2 = os.popen('/sbin/ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read()
    if (len(s1) > 16 or len(s1) < 7):
        MY_IP = s2.strip('\n')
    else:
        MY_IP = s1.strip('\n')

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((MY_IP, udp_port))
    udp_port = udp_socket.getsockname()[1]

    print 'Service location: ({},{})'.format(MY_IP, udp_port)


"""Receive requests from clients!"""
def receive_from_clients():

    global udp_socket
    data, client_info = udp_socket.recvfrom(1024)
    print "Got msg:{} from {}".format(data, client_info)


if __name__ == "__main__":
    init_srv()
    while(True):
        receive_from_clients()
