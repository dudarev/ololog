#!/usr/bin/python
"""
 This file includes some extra functions that are not used in GeoTree at the moment.
 See geohash.py

 This implementation of Geohash http://en.wikipedia.org/wiki/Geohash
 is based on module written by Schuyler Erle
 http://mappinghacks.com/code/geohash.py.txt

 Geohashes are used in the GeoTree as points keys. To shorten the string
 base 64 is used instead of base 32. 
 http://en.wikipedia.org/wiki/Base64
 The length of strings is limited to eight characters by default.

 This results in the following precision:
 4 characters per latitude and longitude, each character is 64 bits, hence
 degree precision is 180 / 64**4. The longest degree is 111 km (longitude on equator).
 Hence, error 111 km * 180 / 64**4 ~ 1e-3 km = 1 m

 Also, to follow GeoTree module convention coordinates are used in the alphabetical
 order (lat,lon).

 Module usage:

 import geohash
 geohash.encode(48,37) # lat,lon
 lat,lon = geohash.decode('0pgwupgw')
"""

class Geostring (object):
    def _to_bits (cls,f,depth=24):
        f *= (1L << depth)
        return [(long(f) >> (depth-i)) & 1 for i in range(1,depth+1)]
    _to_bits = classmethod(_to_bits)

    def bitstring (cls,(x,y),bound=(-180,-90,180,90),depth=24):
        x = cls._to_bits((x-bound[0])/float(bound[2]-bound[0]),depth)
        y = cls._to_bits((y-bound[1])/float(bound[3]-bound[1]),depth)
        bits = reduce(lambda x,y:x+list(y), zip(x,y), [])
        return "".join(map(str,bits))
    bitstring = classmethod(bitstring)

    def __init__ (self, data, bound=(-180,-90,180,90), depth=24):
        self.bound  = bound
        self.depth  = depth
        self.origin = bound[0:2]
        self.size   = (bound[2]-bound[0], bound[3]-bound[1])
        if isinstance(data,tuple) or isinstance(data,list):
            self.hash = self.bitstring(data,bound,depth)
        else:
            self.hash = data

    def __str__ (self):
        return self.hash

    def _to_bbox (self, bits):
        depth = len(bits)/2
        minx = miny = 0.0
        maxx = maxy = 1.0
        for i in range(depth+1):
            try:
                minx += float(bits[i*2])/(2L<<i)
                miny += float(bits[i*2+1])/(2L<<i)
            except IndexError:
                pass
        if depth:
            maxx = minx + 1.0/(2L<<(depth-1))
            maxy = miny + 1.0/(2L<<(depth-1))
        elif len(bits) == 1:
            # degenerate case
            maxx = min(minx + .5, 1.0)
        minx, maxx = [self.origin[0]+x*self.size[0] for x in (minx,maxx)] 
        miny, maxy = [self.origin[1]+y*self.size[1] for y in (miny,maxy)] 
        return tuple([round(x,6) for x in minx, miny, maxx, maxy])

    def bbox (self, prefix=None):
        if not prefix: prefix=len(self.hash)
        return self._to_bbox(self.hash[:prefix])

    def point (self,prefix=None):
        minx, miny, maxx, maxy = self.bbox(prefix)
        return (minx+maxx)/2.0, (miny+maxy)/2.0

    def union (self,other):
        other = str(other)
        hash  = self.hash
        for i in range(min(len(self.hash),len(other))):
            if self.hash[i] != other[i]:
                hash = self.hash[:i]
                break
        return type(self)(hash,self.bound,self.depth)

    __add__ = union

class Geohash (Geostring):
    BASE_64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    @classmethod
    def bitstring (cls,coord,bound=(-180,-90,180,90),depth=24):
        bits = Geostring.bitstring(coord,bound,depth)
        hash = ""
        for i in range(0,len(bits),6):
            m = sum([int(n)<<(5-j) for j,n in enumerate(bits[i:i+6])])
            hash += cls.BASE_64[m]
        return hash

    def bbox (self,prefix=None):
        if not prefix: prefix=len(self.hash)
        bits = [[n>>(5-i)&1 for i in range(6)]
                    for n in map(self.BASE_64.find, self.hash[:prefix])]
        bits = reduce(lambda x,y:x+y, bits, [])
        return self._to_bbox(bits)

def encode(lat,lon):
    "returns hash string 8 characters long, encoded in with base 64"
    # in the original class geo-tuples are in the form (lon,lat)
    return str(Geohash.bitstring((lon,lat)))

def decode(hash):
    "returns tuple (lat,lon)"
    h = Geohash(hash)
    lon,lat = h.point()
    return lat,lon
