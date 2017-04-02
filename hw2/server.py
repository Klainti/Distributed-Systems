from server_API import *

register(1)

init()

ans = int(raw_input("Send reply?[0/1]: "))

reqid = -1
buf = ''
while(1):
    reqid, buf = getRequest(1,buf,1024)
    if (reqid != -1 and ans):
        print "GOT REQUEST:{} with data: {}".format(reqid,buf)
        sendReply (reqid, "", 0)

while(1):
    pass
