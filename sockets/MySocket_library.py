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

    def __init__(self,host,port,verbose):
        self.host=host
        self.port=port
        self.SocketError=SocketError()
        self.verbose=verbose

        try:
            if self.verbose:print 'SocketUtils:Creating Socket()'
            self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error,msg:
            raise SocketError,'Error in Socket Object Creation!!'

    def __str__(self):
        return 'SocketUtils.Socket\nSocket created on Host='+str(self.host)+',Port='+str(self.port)
    
class SocketServer(Socket):

    def __init__(self,host,port,verbose):
        Socket.__init__(self,host,port,verbose)
        self.rport = port
        self.rhost = host
       
        try:
            if self.verbose:print 'SocketUtils:Binding Socket()'
            self.sock.bind((self.host,self.port))
            if self.verbose:print self
        except socket.error,msg:
            raise SocketError,msg
  
  
    def Listen(self,msg='Accepted Connection from:'):
        if self.verbose:print 'Listening to port',self.port
        self.sock.listen(1)
        self.conn,self.rhost=self.sock.accept()
        self.rhost=self.rhost[0]
        if self.rhost:
            if self.verbose:print 'Got connection from',self.rhost
            print msg,self.rhost

    def Send(self,data):
        if self.verbose:print 'Sending data of size ',len(data)
        self.conn.send(data)
        if self.verbose:print 'Data sent!!'
  
    def Receive(self,size):
        if self.verbose:print 'Receiving data...'
        return self.conn.recv(size)
  
    def Close(self):
        if self.verbose:print 'SocketUtils:Closing socket!!'
        self.sock.close()
        if self.verbose:print 'SocketUtils:Socket Closed!!'
  

class SocketClient(Socket):

    def __init__(self,host,port,verbose):
        Socket.__init__(self,host,port,verbose)

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
  
    def Close(self):
        if self.verbose:print 'SocketUtils:Closing socket!!'
        self.sock.close()
        if self.verbose:print 'SocketUtils:Socket Closed!!'
