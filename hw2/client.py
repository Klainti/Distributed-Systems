from discover_multicast import *
import time


setDiscoveryMulticast('127.0.0.1', "224.3.29.71", 10000)

for i in xrange (10):
    print_buffers()
    sendRequest (i%2, "Request for " + str(i%2) )

while (1):
    pass
