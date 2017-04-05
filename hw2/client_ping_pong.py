from client_API import *
import time


send_time = []
reply_time = []
elapsed_time = []

# 224.3.29.71
multicast_ip = raw_input("Give multicast IP:")
multicast_port = int(raw_input("Give multicast port: "))

setDiscoveryMulticast(multicast_ip,multicast_port)

for i in xrange (100):
    reqid = sendRequest (1, "Request nr:" + str(i) )
    send_time.append (time.clock())
    s = getReply(reqid, -1)
    reply_time.append (time.clock())
    time.sleep (0.05)

for i in xrange (100):
    elapsed_time.append (reply_time[i]-send_time[i])

print elapsed_time
