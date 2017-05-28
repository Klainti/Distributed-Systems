"""API about handling cache memory"""

import time
import threading

import packet_struct
import NFS_API

update_cache_lock = threading.Lock()

# Global Variables
cache_mem = {}

# in blocks of 1024K bytes!
SIZE_OF_CACHE = 20

# ................ CACHE API ................ #
"""Insert a block into memory"""
def insert_block(fd, position, data, freshnessT):

    global cache_mem

    update_cache_lock.acquire()

    my_list = [data, time.time(), freshnessT]

    number_of_rows = len(cache_mem)

    # look for empty space in mem
    if (number_of_rows < SIZE_OF_CACHE):
        cache_mem[(fd, position)] = my_list
    else:
        # remove a block first
        remove_block()

        # insert the new block
        cache_mem[(fd, position)] = my_list

    print "IN CACHE: ", cache_mem.keys()

    update_cache_lock.release()

"""Search for a block at given fd,position"""
def search_block(fd, position):

    global cache_mem

    update_cache_lock.acquire()

    pair = (fd, position)

    if (pair in cache_mem.keys()):
        data = cache_mem[pair][0]
        update_cache_lock.release()
        return (True, data)

    update_cache_lock.release()

    return (False, None)

# ................ INTERNAL FUNCTIONS ................ #
def init_cache():
    threading.Thread(target=update_cache_thread).start()


""" Remove a block from memory. The oldest!"""
def remove_block():

    global cache_mem

    older_time = time.time() + 1000
    older_pair = ()

    for pair in cache_mem.keys():

         if (cache_mem[pair][1] < older_time):
             older_pair = pair
             older_time = cache_mem[pair][1]

    del cache_mem[older_pair]


def update_cache_thread():

    while(1):

        print 'WELCOME TO UPDATE CACHE!'

        update_cache_lock.acquire()
        pair_list = cache_mem.keys()

        for pair in pair_list:

            print "Check pair", pair

            time_in_cache = cache_mem[pair][1]
            fressness_time = cache_mem[pair][2]

            # updated block ?
            if (time.time() - time_in_cache > fressness_time):

                print "CACHE UPDATER: ", pair

                data = NFS_API.send_read_and_receive_data(pair[0], pair[1], packet_struct.BLOCK_SIZE)

                # Update cache block
                cache_mem[pair] = [data, time.time(), cache_mem[pair][2]]


        update_cache_lock.release()

        print "Going to sleep"

        time.sleep(1)

'''
                packet_req = packet_struct.construct_read_packet(cur_req_num, pair[0], pair[1], packet_struct.BLOCK_SIZE)

                while(1):

                    # Send packet
                    send_time = time.time()
                    udp_socket.sendto(packet_req, SERVER_ADDR)

                # Wait for reply
                try:
                    reply_packet = udp_socket.recv(1024)
                    req_number, cur_num, total, length, data = struct.unpack(packet_struct.READ_REP_ENCODING, reply_packet)
                    if (req_number == cur_req_num):
                        data = data.strip('\0')

                        # insert into cache
                        cache_API.insert_block(pair[0], pair[1], data, freshness[pair[0]])

                        rec_time = time.time()
                        update_timeout(rec_time-send_time)
                        break
                except socket.timeout:
                    rec_time = time.time()
                    update_timeout(rec_time-send_time)
                    print 'Timeout'

        # end of update process, sleep some time
        update_cache_lock.release()
        time.sleep(1)
'''
