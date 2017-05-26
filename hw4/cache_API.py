"""API about handling cache memory"""

import time

import packet_struct

# Global Variables
cache_mem = {}

# in blocks of 1024K bytes!
SIZE_OF_CACHE = 20

"""Insert a block into memory"""
def insert_block(fd, position, data, freshnessT):

    global cache_mem

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


"""Remove a block from memory. The oldest!"""
def remove_block():

    global cache_mem

    older_time = time.time() + 1000
    older_pair = ()

    for pair in cache_mem.keys():

         if (cache_mem[pair][1] < older_time):
             older_pair = pair
             older_time = cache_mem[pair][1]

    del cache_mem[older_pair]


"""Remove a specific block from cache memory"""
def remove_specific_block(pair):

    global cache_mem
    del cache_mem[pair]


"""Search for a block at given fd,position"""
def search_block(fd, position):

    global cache_mem

    for pair in cache_mem.keys():
        if (pair == (fd, position)):
            return (True, cache_mem[pair][0])


    return (False, None)
