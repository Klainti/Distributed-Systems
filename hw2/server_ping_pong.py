from server_API import *

T = float (raw_input("Sleep time:"))
print T

register(1)

# 224.3.29.71
multicast_ip = raw_input("Give multicast IP:")
multicast_port = int(raw_input("Give multicast port: "))
setDiscoveryMulticast(multicast_ip,multicast_port)

reqid = -1
buf = ''
while(1):
    reqid, buf = getRequest(1,buf,1024)
    s = time.clock()
    time.sleep (T)
    print "Sleep for", time.clock()-s
    sendReply (reqid, str(reqid), len(str(reqid)))


while(1):
    pass
