import NFS_API
import time

# set Server infos!
ipaddr = raw_input("Give server ip: ")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

fd1 = NFS_API.mynfs_open('text10MB.txt', 0, 1000)
print "Return fd: {}".format(fd1)

#print "Send open request"
#fd2 = NFS_API.mynfs_open('index2.png', 0, 1000)
#print "Return fd: {}".format(fd2)

#print "Send open request"
#fd3 = NFS_API.mynfs_open('index3.png', 0, 1000)
#print "Return fd: {}".format(fd3)


sample_image_file1 = open("file10MB.txt")
sample_image1 = sample_image_file1.read()
sample_image_file1.close()

#sample_image_file2 = open("index.png")
#sample_image2 = sample_image_file2.read()
#sample_image_file2.close()

#sample_image_file3 = open("index.png")
#sample_image3 = sample_image_file3.read()
#sample_image_file3.close()


print "Send write request", len(sample_image1)
size1 = NFS_API.mynfs_write(fd1, sample_image1)
print size1

#print "Send write request", len(sample_image2)
#size2 = NFS_API.mynfs_write(fd2, sample_image2)
#print size2


#print "Send write request", len(sample_image3)
#size3 = NFS_API.mynfs_write(fd3, sample_image3)
#print size3




NFS_API.mynfs_seek(fd1, 0)
#NFS_API.mynfs_seek(fd2, 0)
#NFS_API.mynfs_seek(fd3, 0)
'''
stime = time.time()

print "Send read request"
try:
    returned_image1 = NFS_API.mynfs_read(fd1, size1)

    if (len(returned_image1) < size1):
        print "Not received all", len(returned_image1), size1
        returned_image1 += NFS_API.mynfs_read(fd1, size1)
    # print "got msg: {} from read request".format("'"+buf+"'")

    print "Save image"
    new_image1 = open("received_text10MB.txt", "w+")
    new_image1.write(returned_image1)
    new_image1.close()
except NFS_API.TimeoutError:
    print "Too late"

print time.time() -stime
'''
'''
print "Send read request"
try:
    returned_image2 = NFS_API.mynfs_read(fd2, size2)

    if (len(returned_image2) < size2):
        print "Not received all", len(returned_image2), size2
        returned_image2 += NFS_API.mynfs_read(fd2, size2)
    # print "got msg: {} from read request".format("'"+buf+"'")

    print "Save image"
    new_image2 = open("received_image2.png", "w+")
    new_image2.write(returned_image2)
    new_image2.close()
except NFS_API.TimeoutError:
    print "Too late"

print "Send read request"
try:
    returned_image3 = NFS_API.mynfs_read(fd3, size3)

    if (len(returned_image3) < size3):
        print "Not received all", len(returned_image3), size3
        returned_image3 += NFS_API.mynfs_read(fd3, size3)
    # print "got msg: {} from read request".format("'"+buf+"'")

    print "Save image"
    new_image3 = open("received_image3.png", "w+")
    new_image3.write(returned_image3)
    new_image3.close()
except NFS_API.TimeoutError:
    print "Too late"
'''

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
