from server_API import *

register(1)

ans = int(raw_input("Send reply?[0/1]: "))
sleep_time = int(raw_input("Sleep Time: "))
# 224.3.29.71
multicast_ip = raw_input("Give multicast IP:")
multicast_port = int(raw_input("Give multicast port: "))
setDiscoveryMulticast(multicast_ip,multicast_port)

reqid = -1
buf = ''
while(1):
    reqid, buf = getRequest(1,buf,1024)
    if (ans):
        print "GOT REQUEST:{} with data: {} and send reply".format(reqid,buf)
        time.sleep(sleep_time)
        sendReply (reqid, str(reqid), 0)
    elif (reqid != -1):
        print "GOT REQUEST:{} with data: {}".format(reqid,buf)

while(1):
    pass
