from server_API import *

register(1)

ans = int(raw_input("Send reply?[0/1]: "))

# 224.3.29.71
multicast_ip = raw_input("Give multicast IP:")
multicast_port = int(raw_input("Give multicast port: "))
setDiscoveryMulticast(multicast_ip,multicast_port)

reqid = -1
buf = ''
while(1):
    reqid, buf = getRequest(1,buf,1024)
    if (reqid != -1 and ans):
        print "GOT REQUEST:{} with data: {} and send reply".format(reqid,buf)
        sendReply (reqid, "", 0)
    elif (reqid != -1):
        print "GOT REQUEST:{} with data: {}".format(reqid,buf)

while(1):
    pass
