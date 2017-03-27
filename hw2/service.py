''' Register and Unregister a service for a server'''

service_buffer = []


#On success register(append to buffer) return 1, otherwise 0
def register(svcid):
    
    if (svcid not in service_buffer):
        service_buffer.append(svcid)
        return 1
    
    return 0 

#On success unregister(delete from buffer) return 1, otherwise 0
def unregister(svcid):

    if (svcid in service_buffer):
        service_buffer.remove(svcid)
        return 1

    return 0
