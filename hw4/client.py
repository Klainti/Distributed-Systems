import NFS_API
import time

# set Server infos!
ipaddr = raw_input("Give server ip: ")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

print "Send open request"
fd = NFS_API.mynfs_open('image.png', 0, 10)
print "Return fd: {}".format(fd)


sample_image_file = open("index.png")
size = sample_image = sample_image_file.read()
sample_image_file.close()

print "Send write request"
size = NFS_API.mynfs_write(fd, sample_image)

NFS_API.mynfs_seek(fd, 0)


print "Send read request"
returned_image = NFS_API.mynfs_read(fd, size)
if (len(returned_image) < size):
    print "Not received all"
    returned_image += NFS_API.mynfs_read(fd, size)
# print "got msg: {} from read request".format("'"+buf+"'")

new_image = open("returned_image", "w+")
new_image.write(returned_image)
new_image.close()

"""

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

"""
