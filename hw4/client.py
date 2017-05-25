import NFS_API
import time

# set Server infos!
ipaddr = raw_input("Give server ip: ")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

print "Send open request"
fd = NFS_API.mynfs_open('text1.txt', 0, 10)
print "Return fd: {}".format(fd)


print "Send write request"
n = NFS_API.mynfs_write(fd, 'hello world'*400)

NFS_API.mynfs_seek(fd, 0)

stime = time.time()
print "Send read request"
buf = NFS_API.mynfs_read(fd, 3000)
# print "got msg: {} from read request".format("'"+buf+"'")
print len(buf)
print "First time read: ", time.time() - stime

NFS_API.mynfs_seek(fd, 0)

stime = time.time()
print "Send read request"
buf = NFS_API.mynfs_read(fd, 10000)
# print "got msg: {} from read request".format("'"+buf+"'")
print len(buf)
print "Read again the same data: ", time.time() - stime

print "Send read request"
buf = NFS_API.mynfs_read(fd, 10000)
# print "got msg: {} from read request".format("'"+buf+"'")
print len(buf)
