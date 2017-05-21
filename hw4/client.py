import NFS_API

# set Server infos!
ipaddr = raw_input("Give server ip:")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

print "Send open request"
fd = NFS_API.mynfs_open('text.txt', 0, 0)
print "Send read request"
NFS_API.mynfs_read(fd, 10)

print fd
