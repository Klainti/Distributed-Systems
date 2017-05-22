import NFS_API

# set Server infos!
ipaddr = raw_input("Give server ip: ")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

print "Send open request"
fd = NFS_API.mynfs_open('text1.txt', 0, 0)
print "Return fd: {}".format(fd)

print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*40)

print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*40)

print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*40)

print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*40)

print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*40)

NFS_API.mynfs_seek(fd, 0)

print "Send read request"
buf = NFS_API.mynfs_read(fd, 1000)
print "got msg: {} from read request".format("'"+buf+"'")
