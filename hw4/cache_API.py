"""API about handling cache memory"""

import time

import packet_struct

# Global Variables
cache_mem = []

# in blocks of 1024K bytes!
SIZE_OF_CACHE = 20

"""Insert a block into memory"""
def insert_block(fd, position, data, freshnessT):

    global cache_mem

    my_list = [fd, position, data, time.time(), freshnessT]

    number_of_rows = len(cache_mem)

    # look for empty space in mem
    if (number_of_rows < SIZE_OF_CACHE):
        cache_mem.append(my_list)
    else:
        # remove a block first
        remove_block()

        # insert the new block
        cache_mem.append(cache_mem)


"""Remove a block from memory. The oldest!"""
def remove_block():

    global cache_mem

    # sort by the oldest data
    cache_mem = sorted(cache_mem, key=lambda l: l[3])

    del cache_mem[0]


"""Remove a specific block from cache memory"""
def remove_specific_block(mylist):

    global cache_mem
    cache_mem.remove(mylist)


"""Search for a block at given fd,position"""
def search_block(fd, position):

    global cache_mem

    for mem in cache_mem:
        # file that i am looking for
        if (mem[0] == fd):
            # the block i am looking for!
            if (position >= mem[1] and position < mem[1] + packet_struct.BLOCK_SIZE):

                # check the freshness
                time_in_cache = time.time() - mem[3]

                # old one, remove it!
                if (time_in_cache > mem[4]):
                    cache_mem.remove(mem)
                    return (False, None)
                else:
                    cache_mem[cache_mem.index(mem)][3] = time.time()
                    return (True, mem[2])

    return (False, None)
