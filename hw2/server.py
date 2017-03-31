from server_API import *

register(1)

init()

ans = int(raw_input("Send reply?[0/1]: "))

reqid = -1
while(1):
    reqid = getRequest(1,None,None)
    if (reqid != -1 and ans):
        print "GOT REQUEST", reqid
        sendReply (reqid, "", 0)

print reqid

while(1):
    pass
