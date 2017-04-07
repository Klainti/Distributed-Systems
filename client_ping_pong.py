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

sreqid = -1
stime = time.time()
error_packets = 0
getReply_reqid = 0

total_send = 0

try:
    while (1):

        for i in xrange (9):
            send_time.append (time.time())
            reqid = sendRequest (1, "Request nr:" + str(i) )
        total_send += 10

        for i in xrange (9):
            s = getReply(getReply_reqid, -1)
            print "Got reply:", s, "at time", time.time()
            if (s == "ERROR"):
                error_packets += 1
            getReply_reqid += 1
            if (time.time()-stime >= 10):
                print "Received", getReply_reqid-sreqid - 1 - error_packets, "in time", time.time()-stime, "(send)", total_send
                stime = time.time()
                total_send = 0
                sreqid = getReply_reqid
                error_packets = 0
            reply_time.append (time.time())
except KeyboardInterrupt:
    close()
'''
for i in xrange (100):
    elapsed_time.append (reply_time[i]-send_time[i])

print "Max elapsed time:", max (elapsed_time) * 1000
print "Min elapsed time:", min (elapsed_time) * 1000
print "Average elapsed time:", sum(elapsed_time) * 10
elapsed_time.sort()
print "Median elapsed time:", elapsed_time[49] * 1000


close()
'''
