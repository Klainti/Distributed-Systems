from client_API import *
import time


elapsed_time = []

# 224.3.29.71
multicast_ip = raw_input("Give multicast IP: ")
multicast_port = int(raw_input("Give multicast port: "))

svcid = 1
#multicast_ip = "224.3.29.71"
#multicast_port = 10000

setDiscoveryMulticast(multicast_ip,multicast_port)

for i in xrange (100):
    stime = time.time()
    reqid = sendRequest (svcid, "Request for " + str(i) )
    s = getReply(reqid, 5)
    elapsed_time.append (time.time()-stime)

print max (elapsed_time) * 1000
print min (elapsed_time) * 1000

close()
