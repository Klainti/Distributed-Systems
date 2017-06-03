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

    if (freshnessT <= 0):
        return

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


"""Delete the block with given key"""
def delete_block(fd, position):

    global cache_mem

    update_cache_lock.acquire()

    pair = (fd, position)

    del cache_mem[pair]

    update_cache_lock.release()


"""Delete all blocks for a fd"""
def delete_blocks(fd):

    global cache_mem

    update_cache_lock.acquire()

    for pair in cache_mem.keys():

        if (pair[0] == fd):
            del cache_mem[pair]

    update_cache_lock.release()

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

        update_cache_lock.acquire()
        pair_list = cache_mem.keys()

        for pair in pair_list:

            time_in_cache = cache_mem[pair][1]
            fressness_time = cache_mem[pair][2]

            # updated block ?
            if (time.time() - time_in_cache > fressness_time):

                data = NFS_API.send_read_and_receive_data(pair[0], pair[1], packet_struct.BLOCK_SIZE)

                # Update cache block
                cache_mem[pair] = [data, time.time(), cache_mem[pair][2]]


        update_cache_lock.release()

        time.sleep(1)
