#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

from aioredis import StrictRedis
from pybloom_live.pybloom import make_hashfuncs


class RedisBloomFilter(object):
    """
    布隆过滤器，
    """

    def __init__(
            self,
            name,
            capacity=100000000,
            error_ratio=0.0000001,
            redis_host='localhost',
            redis_port=6379,
            redis_password=None,
            redis_db=1,
    ):
        self.name = name
        self.capacity = capacity
        self.error_ratio = error_ratio
        self._redis = StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
        self.num_slices = int(math.ceil(math.log(1.0 / error_ratio, 2)))
        self.bits_per_slice = int(math.ceil(
            (capacity * abs(math.log(error_ratio))) /
            (self.num_slices * (math.log(2) ** 2))))
        self.make_hashes, self.hashfn = make_hashfuncs(self.num_slices, self.bits_per_slice)

    async def is_contains(self, key):
        """Whether a key in filter"""
        hashes = self.make_hashes(key)
        offset = 0
        for k in hashes:
            if not await self._redis.getbit(self.name, offset + k):
                return False
            offset += self.bits_per_slice
        return True

    async def add(self, key):
        """Add a key into filter"""
        hashes = self.make_hashes(key)
        found_all_bits = True
        offset = 0
        for k in hashes:
            if found_all_bits and not await self._redis.getbit(self.name, offset + k):
                found_all_bits = False
            await self._redis.setbit(self.name, offset + k, True)
            offset += self.bits_per_slice

        if not found_all_bits:
            return False
        return True

    def remove(self, key):
        """Remove a key from filter"""
        pass

    async def clear(self):
        """Clear a filter"""
        await self._redis.delete(self.name)

    def __del__(self):
        self._redis.close()
