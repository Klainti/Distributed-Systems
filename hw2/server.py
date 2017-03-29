from server_API import *

register(1)

init()

reqid = -1
while(reqid == -1):
    reqid = getRequest(1,None,None)

print reqid

while(1):
    pass
