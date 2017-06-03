import NFS_API
import time

# set Server infos!
ipaddr = raw_input("Give server ip: ")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

file_name = raw_input("Give filename: ")
server_file_name = "server_" + file_name
received_file_name = "received_" + file_name

freshnessT = int(raw_input("Give freshness: "))

fd = NFS_API.mynfs_open(server_file_name, 0, freshnessT)
print "Return fd: {}".format(fd)

local_fd = open(file_name)
data = local_fd.read()
local_fd.close()

stime = time.time()
print "Send write request", len(data)
size = NFS_API.mynfs_write(fd, data)
print time.time() - stime

NFS_API.mynfs_seek(fd, 0)

stime = time.time()
print "Send read request"
try:
    received_data = NFS_API.mynfs_read(fd, size)

    if (len(received_data) < size):
        print "Not received all", len(received_data), size
        received_data += NFS_API.mynfs_read(fd, size)

    received_fd = open(received_file_name, "w+")
    received_fd.write(received_data)
    received_fd.close()

except NFS_API.TimeoutError:
    print "Too late"

print time.time() -stime


NFS_API.mynfs_close(fd)
