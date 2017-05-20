import NFS_API

# set Server infos!
ipaddr = raw_input("Give server ip:")
port = int(raw_input("Give server port: "))
NFS_API.mynfs_setSrv(ipaddr, port)

NFS_API.udp_socket.sendto("HELLO", NFS_API.SERVER_ADDR)
