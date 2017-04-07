from server_API import *

T =  float(500)/ 1000

register(1)

# 224.3.29.71
multicast_ip = "224.3.29.71"
multicast_port = 10000
setDiscoveryMulticast(multicast_ip,multicast_port)

reqid = -1
buf = ''
while(1):
    reqid, buf = getRequest(1,buf,1024)
    #print "Got reqid", reqid, "at time", time.clock()
    if (T > 0):
        time.sleep (T)
    #print "Send reply", reqid, "at time", time.clock()
    sendReply (reqid, str(reqid), len(str(reqid)))
