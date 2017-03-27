from discover_multicast import *


svcid = int(raw_input("SVCID > "))

setDiscoveryMulticast('127.0.0.1', 0, svcid)

print "?"

for i in xrange (10):

    sendRequest (i%2, "Request for " + str(i%2) )


while (1):
    pass
