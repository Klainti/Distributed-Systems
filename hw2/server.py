from server_API import *

register(1)
register(2)

sleep_time = float(raw_input("Sleep Time(in msec): ")) / 1000
print sleep_time
# 224.3.29.71
multicast_ip = raw_input("Give multicast IP: ")
multicast_port = int(raw_input("Give multicast port: "))
setDiscoveryMulticast(multicast_ip,multicast_port)

reqid = -1
buf = ''

svcid = 1

while(1):
    reqid, buf = getRequest(1)
    #print "GOT REQUEST:{} with data: {} and send reply".format(reqid,buf)
    time.sleep(sleep_time)
    sendReply (reqid, str(reqid), 0)

"""
    if (svcid == 1):
        svcid = 2
    else:
        svcid = 1
"""
while(1):
    pass
