from client_API import *
import time


# 224.3.29.71
multicast_ip = raw_input("Give multicast IP:")
multicast_port = int(raw_input("Give multicast port: "))

setDiscoveryMulticast(multicast_ip,multicast_port)

for i in xrange (10):
    sendRequest (i%2, "Request for " + str(i) )

while (1):
    pass
