"""
    API for FIFO pipe with UDP/IP connection
"""

import sys
#the socket dir contains MySocket_library.py
sys.path.append('../sockets/')
from MySocket_library import *
import socket
import struct
import thread
import time


#Custom Errors
class TimeError(Exception):
   def __init__(self, value):
       self.value = value
   def __str__(self):
       return repr(self.value)

class LengthError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


###############################################################################
################################## CONSTANTS ##################################

#Packets details
ACK_PACKET_SIZE = 16
DATA_PAYLOAD_SIZE = 20
DATA_PACKET_SIZE = DATA_PAYLOAD_SIZE + 12

"""
    data packet encode: ! -> network
                        q -> long long integer (number of packet)
                        s -> string (payload=Data)
                        i -> integer

    ACK packet encode: ! -> network
                       q -> long long integer (number of packet)
                       q -> long long integer (empty spaces)
"""

DATA_ENCODE = '!q' + str(DATA_PAYLOAD_SIZE) + 's' + 'i'
ACK_ENCODE = '!qq'

NPACKET_INDEX = 0
PAYLOAD_INDEX = 1


#waiting time (float) to receive a packet! (in seconds)
TIMEOUT = 1



###############################################################################
################################## VARIABLES ##################################

fd_list = []

################################# <RCV> #################################
#mutex for app. If the packet it requests isnt in the buffer app_wait = 1 and app_wait_mtx.acquire()
rcv_app_wait_mtx = thread.allocate_lock()
rcv_app_wait_mtx.acquire()
rcv_app_wait = 0

#mutex for sychronization between receiving thread and app
rcv_thread_app_mtx = thread.allocate_lock()

#next packet app wants to read from buffer (starts from 1)
rcv_next_app_read = 1
#next packet thread wants to read from socket (starts from 1)
rcv_next_waiting = 1
#number of packets in buffer
rcv_in_buffer = 0
#buffer (dictionary [key: payload])
rcv_buf = {}

rcv_buffer_size = 0
################################# </RCV> #################################


################################# <SEND> #################################
#mutex for app. If buffer full, app_wait = 1 and app_wait_mtx.acquire()
snd_app_wait_mtx = thread.allocate_lock()
snd_app_wait_mtx.acquire()
snd_app_wait = 0

snd_thread_wait_mtx = thread.allocate_lock()
snd_thread_wait_mtx.acquire()
snd_thread_wait = 0

#mutex for sychronization between sending thread and app
snd_thread_app_mtx = thread.allocate_lock()

#next packet app wants to read from buffer (starts from 1)
snd_next_app_write = 1
#next packet thread wants to read from socket (starts from 1)
snd_next_sending = 1
#number of packets in buffer
snd_in_buffer = 0
#buffer (dictionary [key: payload])
snd_buf = {}

snd_buffer_size = 0

end_of_trans = 0

close_mtx = thread.allocate_lock()
close_mtx.acquire()
################################# </SEND> #################################



###############################################################################
################################## FUNCTIONS ##################################




############################ <PACKET FUNCTIONS> ############################
""" packet format: data_packet --> [number_of_packet,data,len_of_valid_data]
                   ack_packet  --> [number_of_packet,next_number_sequence]
                   rtt_packet  --> [RTT]
"""
def construct_packet(encode, number_of_packet, payload, size_of_valid_data):
    if (encode == '!qq'):
        return struct.pack(encode,number_of_packet,payload)
    else:
        return struct.pack(encode,number_of_packet,payload,size_of_valid_data)

def deconstruct_packet(decode, packet):
    try:
        if (decode == '!qq'):
            return struct.unpack(decode,packet)
        else:
            npacket , data , len_valid_data = struct.unpack(decode,packet)
            return (npacket,data[:len_valid_data])

    except struct.error:
        raise LengthError
############################ </PACKET FUNCTIONS> ############################




##################### <PRIVATE FUNCTION FOR THREADS> #####################
#receive packet with timeout!
def packet_receive(sock, size_of_packet, decode):

        #wait for next packet
        try:
            return_packet = sock.ReceiveFrom(size_of_packet)

            #In case the packet is broken deconstuct_packet returns LengthError
            try:
                data = deconstruct_packet(decode,return_packet[0])
            except LengthError:
                raise LengthError ("Received broken packet")

            addr = return_packet[1]
            return (data,addr)

        except socket.timeout:
                raise TimeError ("Packet lost")
##################### </PRIVATE FUNCTION FOR THREADS> #####################



############################ <THREADS CODE> ############################
def rcv_thread (sock):


    global rcv_next_waiting
    global rcv_next_app_read
    global rcv_in_buffer
    global rcv_buffer_size


    num_of_packets = 1

    while (True):

        missed = 0

        for p in xrange (num_of_packets):

            try:
                data, addr = packet_receive(sock, DATA_PACKET_SIZE, DATA_ENCODE)
            except:
                missed += 1
                continue

            print "RCV_THREAD: got", data

            rcv_thread_app_mtx.acquire()

            #Check if packet key is within window [rcv_next_waiting - rcv_next_waiting + num_of_packets] and buffer has empty space in order to save its
            if (data[NPACKET_INDEX] >= rcv_next_waiting and data[NPACKET_INDEX] <= rcv_next_waiting + num_of_packets and data[NPACKET_INDEX]-rcv_next_waiting < rcv_buffer_size-rcv_in_buffer):

                #Not allowed duplicate packets
                if (not rcv_buf.has_key(data[NPACKET_INDEX])):
                    rcv_buf.update( {data[NPACKET_INDEX]: data[PAYLOAD_INDEX]} )

                    rcv_in_buffer += 1
                    print "Rcv_thread: Received packet" ,data[NPACKET_INDEX] , "(in:", rcv_in_buffer, ")"

                    print "Rec Buffer:", rcv_buf

            rcv_thread_app_mtx.release()


        #Not a single packet received
        if (missed == num_of_packets):
            continue

        rcv_thread_app_mtx.acquire()

        #Find the first missing packet
        while (rcv_buf.has_key(rcv_next_waiting)):
            rcv_next_waiting += 1

        #In case buffer is full we send 1 empty space instead of 0
        num_of_packets = max(1, rcv_buffer_size - rcv_in_buffer)

        #send ACK for next num_of_packets packets
        ack_packet = construct_packet(ACK_ENCODE, rcv_next_waiting, num_of_packets,None)
        sock.SendTo(ack_packet,addr)

        print "RCV_THREAD: Send ACK with seq number: ", rcv_next_waiting, "and num_of_packets: ", num_of_packets


        #if app waits give it priority
        if (rcv_app_wait and rcv_next_app_read < rcv_next_waiting):
            rcv_app_wait_mtx.release()
        else:
            rcv_thread_app_mtx.release()



def snd_thread (sock):

    global snd_next_sending
    global snd_in_buffer
    global snd_app_wait
    global snd_thread_wait
    global end_of_trans

    num_of_packets = 1

    while (True):

        #DEN TO XRHSIMOPOIOUME. ANT NA STELNOUME ENA AN DEN LAVEI ACK EMEIS TA KSANASTELNOUME OLA. MPOROUME NA TO KRATHSOUME KAI ETSI
        send_one = False

        snd_thread_app_mtx.acquire()


        #Waits till buffer has at least num_of_packets packets (if num_of_packets > buffer_size we reduce num_of_packets to buffer_size)
        #Except if close has been called (end_of_trans == 1) which means we must send the remaining packets
        while (snd_in_buffer < min(num_of_packets, snd_buffer_size) and (not end_of_trans) ):
            print "SND_THREAD: Wait for new packet"
            snd_thread_app_mtx.release()
            snd_thread_wait = 1
            snd_thread_wait_mtx.acquire()
            snd_thread_app_mtx.acquire()
            snd_thread_wait = 0


        #Send num_of_packets packets
        for i in xrange (num_of_packets):

            #Next packet is missing (when we send the last packets)
            if (snd_buf.has_key(snd_next_sending+i)):
                #Send next packet
                print "SND_THREAD: Sending packet", snd_next_sending+i
                sock.Send(snd_buf[snd_next_sending+i])



        #Wait for ACK
        try:
            ack = packet_receive(sock, ACK_PACKET_SIZE, ACK_ENCODE)[0]
            print "SND_THREAD: Took ack with seq_num: ", ack[0], "and empty_spaces: ", ack[1]

            #Update buffer
            for i in xrange (snd_next_sending, ack[0]):
                del snd_buf[i]
                snd_in_buffer -= 1

            if (end_of_trans and snd_in_buffer == 0):
                break

            #Update variables
            snd_next_sending = ack[0]
            num_of_packets = ack[1]

        except TimeError, LengthError:
            #ACK not received
            #send only one packet
            print 'ACK not received'
            send_one = True

        if (snd_app_wait == 1):
            snd_app_wait_mtx.release()

        snd_thread_app_mtx.release()

    print "RCV_THREAD: End of transmision"
    close_mtx.release()
############################ </THREADS CODE> ############################




############################ <BASIC LIBRARY FUNCTIONS> ############################

#Open reading side of pipe. Return a positive integer as file discriptor
def netfifo_rcv_open(port,bufsize):

    #initial buffer
    global rcv_buffer_size
    rcv_buffer_size = bufsize

    #create Server object (reading side)
    socket_object = SocketServer(socket.AF_INET, socket.SOCK_DGRAM, TIMEOUT, Hostname(), port, 0)

    #start the thread
    thread.start_new_thread (rcv_thread, (socket_object, ))

    fd_list.append(socket_object)

    return fd_list.index(socket_object)

#reading from pipe. Return data.
def netfifo_read(fd,size):

    global rcv_next_app_read
    global rcv_app_wait
    global rcv_in_buffer
    global rcv_buffer_size

    s = ""

    #while (len(s) < min(rcv_buffer_size*DATA_PAYLOAD_SIZE, size/DATA_PAYLOAD_SIZE * DATA_PAYLOAD_SIZE)):

    while (len(s)<size):
        #app wants to read packet next_app_read
        rcv_thread_app_mtx.acquire()

        while (rcv_next_app_read not in rcv_buf):
            #if packet not in buf wait
            print "READ_APP: waits for packet " ,rcv_next_app_read
            rcv_app_wait = 1
            rcv_thread_app_mtx.release()
            rcv_app_wait_mtx.acquire()
            rcv_app_wait = 0


        d = rcv_buf[rcv_next_app_read]
        rcv_next_app_read += 1
        rcv_in_buffer -= 1
        del rcv_buf[rcv_next_app_read-1]
        print "READ_APP: got packet", rcv_next_app_read-1

        rcv_thread_app_mtx.release()

        if (d == ""):
            break

        s = s + d
        print "READ_APP: has till now: ", s



    return s

#close reading side
def netfifo_rcv_close(fd):
    sock = fd_list[fd]
    sock.Close()





#Open writing side of pipe. Return a positive integer as file discriptor
def netfifo_snd_open(host,port,bufsize):

    #initial buffer
    global snd_buffer_size
    snd_buffer_size = bufsize

    #create Server object (writing side)
    socket_object = SocketClient(socket.AF_INET, socket.SOCK_DGRAM, TIMEOUT, 0)
    socket_object.Connect(host,port)

    #start the snd_thread
    thread.start_new_thread (snd_thread, (socket_object, ))

    fd_list.append(socket_object)

    return fd_list.index(socket_object)


#writing data in pipe
def netfifo_write(fd,buf,size):

    global snd_next_app_write
    global snd_in_buffer
    global snd_thread_wait
    global snd_buffer_size
    global snd_app_wait

    for s in xrange (0, size, DATA_PAYLOAD_SIZE):

        packet = construct_packet(DATA_ENCODE,snd_next_app_write, buf[s: s+ DATA_PAYLOAD_SIZE],len(buf[s: s+ DATA_PAYLOAD_SIZE]))

        snd_thread_app_mtx.acquire()

        print "WRITE_APP: tries to add packet", snd_next_app_write

        while (snd_in_buffer == snd_buffer_size):
            print "WRITE_APP: waits for empty position"
            snd_app_wait = 1
            snd_thread_app_mtx.release()
            snd_app_wait_mtx.acquire()
            snd_thread_app_mtx.acquire()
            snd_app_wait = 0

        snd_buf.update ({snd_next_app_write: packet})

        snd_next_app_write += 1
        snd_in_buffer += 1

        print "WRITE_APP: added packet", snd_next_app_write-1,"(in:", snd_in_buffer, ")"

        if (snd_thread_wait == 1):
            snd_thread_wait_mtx.release()

        snd_thread_app_mtx.release()


#close writing side
def netfifo_snd_close(fd):

    sock = fd_list[fd]

    global end_of_trans
    global snd_thread_wait

    netfifo_write (fd, "", 1)

    snd_thread_app_mtx.acquire()

    end_of_trans = 1

    if (snd_thread_wait == 1):
        snd_thread_wait_mtx.release()

    snd_thread_app_mtx.release()

    close_mtx.acquire()

    sock.Close()

############################ </BASIC LIBRARY FUNCTIONS> ############################
