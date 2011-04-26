#!/usr/bin/python
"""
 Module usage:

 import geohash
 geohash_str = geohash.encode(48,37) # lat,lon

 This implementation of Geohash http://en.wikipedia.org/wiki/Geohash
 is based on module written by Schuyler Erle
 http://mappinghacks.com/code/geohash.py.txt

 At the moment of writing it was not clear if decoding methods will be used in
 GeoTree module. All the relevant functions are moved to geohash_extended.py and
 this file is kept as short as possible. Also moved are union, bounding box methods.

 Geohashes are used in the GeoTree as points keys. To shorten the string
 base 64 is used instead of base 32. 
 http://en.wikipedia.org/wiki/Base64
 '+/' are replaced with '-_' to leave the key URI-friendly.

 The length of strings is limited to eight characters.

 This results in the following precision:
 4 characters per latitude and longitude, each character is 64 bits, hence
 degree precision is 180 / 64**4. The longest degree is 111 km (longitude on equator).
 Hence, error 111 km * 180 / 64**4 ~ 1e-3 km = 1 m

 Also, to follow GeoTree module convention coordinates are used in the alphabetical
 order (lat,lon).
"""

__author__ = 'Artem Dudarev'
__credits__ = 'Schuyler Erle'
__licence__ = 'Apache 2.0'
__date__ = 'Tue 09 Mar 2010 06:55:50 PM EET'


class Geostring (object):
    @classmethod
    def _to_bits (cls,f,depth=24):
        f *= (1L << depth)
        return [(long(f) >> (depth-i)) & 1 for i in range(1,depth+1)]

    @classmethod
    def bitstring (cls,(x,y),bound=(-180,-90,180,90),depth=24):
        x = cls._to_bits((x-bound[0])/float(bound[2]-bound[0]),depth)
        y = cls._to_bits((y-bound[1])/float(bound[3]-bound[1]),depth)
        bits = reduce(lambda x,y:x+list(y), zip(x,y), [])
        return "".join(map(str,bits))


class Geohash (Geostring):
    BASE_64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    @classmethod
    def bitstring (cls,coord,bound=(-180,-90,180,90),depth=24):
        # depth 24 is 24 bits per coordinate - 24/6 = 4 characters in base 64
        # 4+4 = 8 total length of the geohash
        bits = Geostring.bitstring(coord,bound,depth)
        hash = ""
        # here "magic" numbers are related to base 64 = 2**6
        # << - bit shift operator
        for i in range(0,len(bits),6):
            m = sum([int(n)<<(5-j) for j,n in enumerate(bits[i:i+6])])
            hash += cls.BASE_64[m]
        return hash


def encode(lat,lon):
    "returns geohash string 8 characters long, encoded with base 64"
    # in the original class geo-tuples are in the form (lon,lat)
    return Geohash.bitstring((lon,lat))

def encode_coord_str(coord_str):
    "same as above only accepts a string 'lat,lon' or as GeoPt"
    if type(coord_str) == type(u'unicode') or type(coord_str) == type('string'):
        lat,lon = map(float,coord_str.split(','))
    else:
        lat = coord_str.lat
        lon = coord_str.lon
    return Geohash.bitstring((lon,lat))
