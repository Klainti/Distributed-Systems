from client_API import *
import time


send_time = []
reply_time = []
elapsed_time = []

multicast_ip = "224.3.29.71"
multicast_port = 10000
# 224.3.29.71
#multicast_ip = raw_input("Give multicast IP:")
#multicast_port = int(raw_input("Give multicast port: "))

setDiscoveryMulticast(multicast_ip,multicast_port)

for i in xrange (100):
    send_time.append (time.clock())
    reqid = sendRequest (1, "Request nr:" + str(i) )

    s = getReply(reqid, -1)
    reply_time.append (time.clock())
    time.sleep (0.05)

for i in xrange (100):
    elapsed_time.append (reply_time[i]-send_time[i])

print "Max elapsed time:", max (elapsed_time) * 1000
print "Min elapsed time:", min (elapsed_time) * 1000
print "Average elapsed time:", sum(elapsed_time) * 10
elapsed_time.sort()
print "Median elapsed time:", elapsed_time[49] * 1000


close()
