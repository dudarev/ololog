#!/usr/bin/python2.5

"""math utilities used in geotree
"""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'
__date__ = 'Mon 15 Mar 2010 10:51:02 AM EET'


import math

def lat_lon_to_tile(lat,lon,z):
    """convert a Point to tuple (x,y,z) representing a tile in Mercator projection
   
    information about converting coordinates to a tile in Mercator projection may be found at:
    http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    http://mapki.com/wiki/Lat/Lon_To_Tile
    """

    lat_rad = math.radians(lat)
    n = 2.0 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)

    return (x,y,z)

def tile_to_lat_lon(x, y, z):
    """returns NW corner of a tile

    http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#tile_numbers_to_lon.2Flat_2 
    """

    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)

    return(lat_deg, lon_deg)

def can_take_str(f):
    """function to decorate tile_children and tile_parent below
    so that they may accept a string or three integer arguments"""
    def f_with_args_converted(*args,**kwargs):
        if isinstance(args[0],str) or isinstance(args[0],unicode):
            args = map(int,args[0].split(',')[:3]) + args[0].split(',')[3:]
        return f(*args,**kwargs)
    return f_with_args_converted 

def tile_tuple_to_str(t):
    return '%d,%d,%d' % t

def tile_str_to_tuple(s):
    return tuple(map(int,s.split(',')[:3]))

@can_take_str
def tile_children(*args,**kwargs):
    """subtiles for a given tile for next zoom
    
    see: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Subtiles
    
    returns either list of tuples (x,y,z) if return_str = False
    or list of strings "x,y,z" if return_str = True
    """

    x,y,z = args[:3]
    extra = args[3:]
    children = ( (2*x, 2*y, z+1),
                 (2*x+1, 2*y, z+1),
                 (2*x,2*y+1,z+1),
                 (2*x+1,2*y+1,z+1) )

    if kwargs.get('return_str',False):
        if extra:
            return map(lambda x: tile_tuple_to_str(x)+','+','.join(extra),children)
        else:
            return map(tile_tuple_to_str,children)
    return children

@can_take_str
def tile_parent(*args,**kwargs):
    """return tile to which x,y,z belongs for smaller zoom (z-1)
    
    returns either tuple (x,y,z) if return_str = False
    or string "x,y,z" if return_str = True
    """

    x,y,z = args[:3]
    extra = args[3:]
    parent = ( int(x/2), int(y/2), z-1 )

    if kwargs.get('return_str',False):
        if extra:
            return tile_tuple_to_str(parent)+','+','.join(extra)
        else:
            return tile_tuple_to_str(parent)
    return parent
