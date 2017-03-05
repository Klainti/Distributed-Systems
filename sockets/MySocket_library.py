""" Socket utilities class
    created by Amey R Pathak
    contains SocketServer,SocketClient classes
    link: http://code.activestate.com/recipes/200946-a-quick-and-dirty-client-and-server-socket-class/

    ***Modified by Klainti Bontourri && Panagiotis S. Chytas
    for the purpose of CE-323 Distributed Systems projects***
"""

import socket
def Hostname():
    return socket.gethostname()


class SocketError(Exception):
    pass

class Socket:

    def __init__(self,family,socket_type,timeout,verbose):
        self.SocketError=SocketError()
        self.verbose=verbose

        try:
            if self.verbose:print 'SocketUtils:Creating Socket()'
            self.sock=socket.socket(family,socket_type)
        except socket.error,msg:
            raise SocketError,'Error in Socket Object Creation!!'

        #set timeout for Receive!
        self.sock.settimeout(timeout)
 
    def Close(self):
        if self.verbose:print 'SocketUtils:Closing socket!!'
        self.sock.close()
        if self.verbose:print 'SocketUtils:Socket Closed!!'
  

    def __str__(self):
        return 'SocketUtils.Socket\nSocket created on Host='+str(self.host)+',Port='+str(self.port)
    
class SocketServer(Socket):

    def __init__(self,family,socket_type,timeout,host,port,verbose):
        Socket.__init__(self,family,socket_type,timeout,verbose)
        self.host= host
        self.port= port

        try:
            if self.verbose:print 'SocketUtils:Binding Socket()'
            self.sock.bind((self.host,self.port))
            if self.verbose:print self
        except socket.error,msg:
            raise SocketError,msg
  
  
    def Listen(self,msg='Accepted Connection from:'):
        if self.verbose:print 'Listening to port',self.port
        self.sock.listen(1)
        self.conn,self.addr = self.sock.accept()
        self.addr = self.addr[0]
        if self.addr:
            if self.verbose:print 'Got connection from',self.addr
            print msg,self.addr

    def Send(self,data):
        if self.verbose:print 'Sending data of size ',len(data)
        self.conn.send(data)
        if self.verbose:print 'Data sent!!'
  
    def Receive(self,size):
        if self.verbose:print 'Receiving data...'
        return self.conn.recv(size)

    def ReceiveFrom(self,size):
        if self.verbose:print 'Receiving data from...'
        return self.sock.recvfrom(size)

    def SendTo(self,data,addr):
        if self.verbose:print 'Send data to' + str(addr)
        self.sock.sendto(data,addr)


 
class SocketClient(Socket):

    def __init__(self,family,socket_type,timeout,verbose):
        Socket.__init__(self,family,socket_type,timeout,verbose)

    def Connect(self,rhost,rport):
        self.rhost,self.rport=rhost,rport

        try:
            if self.verbose:print 'Connecting to '+str(self.rhost)+' on port '+str(self.rport)
            self.sock.connect((self.rhost,self.rport))
            if self.verbose:print 'Connected !!!'
        except socket.error,msg:
            raise SocketError,'Connection refused to '+str(self.rhost)+' on port '+str(self.rport)            


    def Send(self,data):
        if self.verbose:print 'Sending data of size ',len(data)
        self.sock.send(data)
        if self.verbose:print 'Data sent!!'
  
    def Receive(self,size):
        if self.verbose:print 'Receiving data...'
        return self.sock.recv(size)

    def ReceiveFrom(self,size):
        if self.verbose:print 'Receiving data from...'
        return self.sock.recvfrom(size)

    def SendTo(self,data,host,port):
        if self.verbose:print 'Send data to' + str(host)
        self.sock.sendto(data,(host,port))

