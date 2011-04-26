#!/usr/bin/python2.5

"""GeoTree stores point geographic entities. 
Depending on zoom level, it returns the most important ones. 
Importance is determined by a property of a point. 
It may be, for instance, population of a city, entity update time etc.
"""

__version__ = '0.5'
__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'

from google.appengine.ext import db

from sorted_lists import sorted_tiles_set, sorted_points_list, sorted_points_list_limited
from geomath import lat_lon_to_tile, tile_parent, tile_children, tile_str_to_tuple, tile_tuple_to_str
import geohash

import logging

from django.utils import simplejson as json

import config

from google.appengine.api import memcache

""" stylistic convention: geographical variables are used in alphabetical order, 
i.e. lat,lon for coordinates, and x,y,z for tiles
"""

""" TODO: 

    add memcaching
        http://blog.notdot.net/2009/9/Efficient-model-memcaching
        see also implementation of sharded counter using memcache
        http://www.billkatz.com/2008/10/Fault-tolerant-counters-for-App-Engine
        http://github.com/DocSavage/sharded_counter/blob/master/counter.py
        and
        http://code.google.com/appengine/articles/sharding_counters.html

    zoom-dependent importance
    (probably not... but tree dependent zoom_max, zoom_min...)
        a city point may have large importance at zoom 10 than at zoom 15
        initial zoom for a point: such zoom so that for larger zooms 
        do not store that point in tiles
        new property for tiles that does not have limitation on number of
        points in it
            tile.points_native = TextProperty(json(list(dict)))
        geomath method that returns based on
            lat,lon,size -> maximum zoom for a tile with larger sizes

    errors handling
        when geohash of a new point already exists (this means that coordinates are
        the same within 1 meter)
"""

def get_max_z(gt_key_name):
    """for a GeoTree get max_z (either from datastore or memcache)"""
    memcache_key = "%s max_z" % gt_key_name 
    max_z = memcache.get(memcache_key)
    if max_z is None:
        max_z = GeoTree.get(gt_key_name).max_z
        memcache.set(memcache_key, max_z)
    return max_z

def get_min_z(gt_key_name):
    """for a GeoTree get min_z (either from datastore or memcache)"""
    memcache_key = "%s min_z" % gt_key_name 
    min_z = memcache.get(memcache_key)
    if min_z is None:
        min_z = GeoTree.get(gt_key_name).min_z
        memcache.set(memcache_key, min_z)
    return min_z


class Point(db.Model):
    """inherit your points from this class"""

    coord = db.GeoPtProperty()
    importance = db.FloatProperty(default=1.0)
    name = db.StringProperty()
    
    """ TODO:
        update
        delete
    """

    def __init__(self, *args, **kwargs):
        # http://groups.google.com/group/google-appengine/browse_thread/thread/0a885d8af6dc046f
        if (not 'key_name' in kwargs) and (not 'key' in kwargs):
            if kwargs.has_key('coord'):
                key_name=geohash.encode_coord_str(kwargs['coord'])
                super(Point, self).__init__(key_name=key_name, **kwargs)
        else:
            super(Point, self).__init__(**kwargs)

    def insert_to_tile(self, gt_key_name=None, max_z=None):
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY
        if not max_z:
            max_z = get_max_z(gt_key_name)
        x,y,z = lat_lon_to_tile(self.coord.lat, self.coord.lon, max_z)
        tile_key_name = '%d,%d,%d,%s' % (x,y,z,gt_key_name)
        t = Tile.get_by_key_name(tile_key_name)
        if not t:
            t = Tile(x=x, y=y, z=z, key_name=tile_key_name, gt_key_name=gt_key_name)
        point_dict = {'key_name':self.key().name(),'importance':self.importance,'coord':(self.coord.lat,self.coord.lon),'name':self.name}
        if t.points_native:
            # use sorted list because this is used during merging of tiles
            points_native = sorted_points_list(json.loads(t.points_native))
            points_native.insert(point_dict)
            t.points_native = json.dumps(points_native)
        else:
            points_native = [point_dict]
            t.points_native = json.dumps(points_native)
        t.put()
        return tile_key_name

    def update_importance(self, importance_new, gt_key_name=None, max_z=None):
        """updates importance of the point and the maximum zoom tile, other tiles are not updated"""
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY
        if not max_z:
            max_z = get_max_z(gt_key_name)
        self.importance = importance_new
        self.put()
        x,y,z = lat_lon_to_tile(self.coord.lat, self.coord.lon, max_z)
        tile_key_name = '%d,%d,%d,%s' % (x,y,z,gt_key_name)
        t = Tile.get_by_key_name(tile_key_name)
        if t:
            if t.points_native:
                points_native = json.loads(t.points_native)
                self_key_name = self.key().name()
                for p in points_native:
                    if p['key_name'] == self_key_name:
                        p['importance'] = importance_new
                        t.points_native = json.dumps(sorted_points_list(points_native))
                        break
                t.put()
        GeoTree.mark_tile_updated(tile_key_name, gt_key_name)


class Tile(db.Model):
    "key name is a string - 'x,y,z,gt_key_name'"
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    z = db.IntegerProperty()
    gt_key_name = db.StringProperty()
    # json list of dicts: key_name, importance, coord, name
    # limited sorted list
    points = db.TextProperty(default=None)
    # unlimited list with points initially added to this tile
    points_native = db.TextProperty(default=None)

    def __repr__(self):
        return "Tile: %d %d %d" % (self.x, self.y, self.z)


class GeoTree(db.Model):
    """
    list of just updated tiles which parents are not updated yet
    total number of points
    """

    tiles_updated = db.StringListProperty(default=[])
    number_points = db.IntegerProperty(default=0)
    max_z = db.IntegerProperty(default=config.MAX_Z)
    min_z = db.IntegerProperty(default=config.MIN_Z)

    # default geo tree key (in apps use something like "osm", "cities", "c" etc.)
    _GEO_TREE_KEY = 'gt'

    # stylistic convention here:
    # implement request methods as @staticmethod
    # implement methods that change the GeoTree datastore entry as @classmethod

    def __init__(self, *args, **kwargs):
        "by default GeoTree initializes with key_name=self._GEO_TREE_KEY"
        if (not 'key_name' in kwargs) and (not 'key' in kwargs):
            kwargs['key_name'] = self._GEO_TREE_KEY
        super(GeoTree, self).__init__(*args, **kwargs)

    @staticmethod
    def get(gt_key_name=None):
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY
        "return info"
        gt = GeoTree.get_by_key_name(gt_key_name)
        if gt: return gt 
        return None 

    @staticmethod
    def exists(gt_key_name=None):
        "checks if GeoTree exists"
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY
        gt = GeoTree.get_by_key_name(gt_key_name)
        if gt: return True
        return False

    @staticmethod
    def fetch_around_tile(tile_center_str, gt_key_name=None):
        """returns JSON text of all important points in tiles around center tile"""
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY

        tiles = []

        # a square 3x3 tiles around center tile
        dx = 1
        dy = 1

        xc,yc,z = tile_str_to_tuple(tile_center_str)
        xend = 2**z-1
        ymin = max(0,yc-dy)
        ymax = min(xend,yc+dy)
        xmin = xc - dx
        if xmin < 0:
            xmin = xend + 1 + xmin
        xmax = xc + dx
        if xmax > xend:
            xmax = xmax - xend - 1

        for y in range(ymin,ymax+1):
            if xmin > xmax:
                # if go beyond 360 degrees
                tiles.extend(Tile.all().filter('gt_key_name', gt_key_name).filter('z',z).filter('y',y).filter('x >=',xmin).filter('x <=',xend).order('-x').fetch(xend-xmin+1))
                tiles.extend(Tile.all().filter('gt_key_name', gt_key_name).filter('z',z).filter('y',y).filter('x >=', 0).filter('x <=',xmax).order('-x').fetch(xmax-0+1))
            else:
                tiles.extend(Tile.all().filter('gt_key_name', gt_key_name).filter('z',z).filter('y',y).filter('x >=',xmin).filter('x <=',xmax).order('-x').fetch(xmax-xmin+1))

        if not tiles:
            return '[]'

        # not to convert from JSON and than back, the JSON string is formatted directly
        # [1:-1] below to get rid of '[' and ']' - seems like dirty hack - think about refactoring
        tiles_points_json = "["

        for t in tiles:
            # check that lists are not empty: not None and longer than '[]'
            if t.points_native and len(t.points_native)>2:
                tiles_points_json += t.points_native[1:-1]+','
            if t.points and len(t.points)>2:
                tiles_points_json += t.points[1:-1]+','

        # [:-1] to get rid of last ','
        return tiles_points_json[:-1]+"]"

    @classmethod
    def mark_tile_updated(cls, tile_key_name, gt_key_name=None):
        """Insert points that are not in the GeoTree."""
        if not gt_key_name:
            gt_key_name = cls._GEO_TREE_KEY
        gt = cls.get_by_key_name(gt_key_name)
        if gt:
            tiles = sorted_tiles_set(gt.tiles_updated)
            tiles_new = sorted_tiles_set([tile_key_name])
            tiles.extend(tiles_new)
            gt.tiles_updated = list(tiles)
        else:
            gt = cls(key_name=gt_key_name, number_points = len(points_list), tiles_updated = list(sorted_tiles_set(tile_keys)) )
        gt.put()

    @classmethod
    def insert_points_list(cls, points_list, gt_key_name=None, max_z=None):
        """Insert points that are not in the GeoTree."""
        if not gt_key_name:
            gt_key_name = cls._GEO_TREE_KEY
        tile_keys = []
        for p in points_list:
            tile_keys.append(p.insert_to_tile(gt_key_name=gt_key_name, max_z=max_z))

        gt = cls.get_by_key_name(gt_key_name)
        if gt:
            gt.number_points += len(points_list)
            tiles = sorted_tiles_set(gt.tiles_updated)
            tiles_new = sorted_tiles_set(tile_keys)
            tiles.extend(tiles_new)
            gt.tiles_updated = list(tiles)
        else:
            gt = cls(key_name=gt_key_name, number_points = len(points_list), tiles_updated = list(sorted_tiles_set(tile_keys)) )
        gt.put()
        return True

    @staticmethod
    def update_tile(tile_key_name, children_updated_list, gt_key_name=None):
        """Updates a single tile, returns Tile model corresponding to tile_str. Datastore is not updated."""
        if not gt_key_name:
            gt_key_name = GeoTree._GEO_TREE_KEY
        t = Tile.get_by_key_name(tile_key_name)
        if not t:
            x,y,z = tile_str_to_tuple(tile_key_name)
            t = Tile(x=x, y=y, z=z, gt_key_name=gt_key_name, key_name=tile_key_name)
        points = sorted_points_list_limited([])
        for child_tile_key_name in children_updated_list:
            ct = Tile.get_by_key_name(child_tile_key_name)
            if ct:
                # in order insert points from child tile to parent
                # stop when does not insert any more

                # TODO: refactor to a single function
                # from native points
                if ct.points_native:
                    for p in json.loads(ct.points_native):
                        if not points.insert(p):
                            break

                # from points
                if ct.points:
                    for p in json.loads(ct.points):
                        if not points.insert(p):
                            break

                t.points = (json.dumps(points))

        return t

    @classmethod
    def update_tiles(cls, count=config.COUNT_UPDATE, gt_key_name=None):
        """Update several tiles and puts them into datastore."""
        if not gt_key_name:
            gt_key_name = cls._GEO_TREE_KEY
        gt = cls.get_by_key_name(gt_key_name)
        if gt:

            # check if the first tile has larger z than min_z, if not - nothing to update
            logging.debug(gt_key_name)
            logging.debug(gt.tiles_updated)
            x,y,z = tile_str_to_tuple(gt.tiles_updated[0])
            min_z = get_min_z(gt_key_name)
            if not (z > min_z):
                r = '\n\nInfo: updated 0 tiles, nothing to update'
                return r

            needs_update = True
            count_updated = 0

            while count_updated < count and needs_update:
                # get a group of tiles with a common parent (starting with the first)
                first_tile = gt.tiles_updated[0]
                p = tile_parent(first_tile,return_str=True)
                c = tile_children(p,return_str=True)
                c_in_updated = [first_tile]
                for t in gt.tiles_updated[1:]:
                    if t in c:
                        c_in_updated.append(t)
                # update parent, use all children for update
                t = cls.update_tile(p, c, gt_key_name=gt_key_name)
                t.put()
                # remove the group of updated children tiles from tiles_updated
                tiles_updated = sorted_tiles_set(gt.tiles_updated)
                tiles_updated.remove(c_in_updated)
                # insert updated tile
                tiles_updated.insert(p)
                gt.tiles_updated = list(tiles_updated)
                gt.put()
                # check if the first tile has smaller z than min_z, if not needs_update = False
                x,y,z = tile_str_to_tuple(tiles_updated[0])
                min_z = get_min_z(gt_key_name)
                if z == min_z:
                    needs_update = False 
                # increase count_updated
                count_updated += 1
        else:
            return '\n\nError: no GeoTree exists'

    @classmethod
    def remove_point_by_key_name(cls, key_name, gt_key_name=None, max_z=None):
        #delete from native tile
        if not gt_key_name:
            gt_key_name = cls._GEO_TREE_KEY
        if not max_z:
            max_z = get_max_z(gt_key_name)
        p = Point.get_by_key_name(key_name)
        tile_str = tile_tuple_to_str(lat_lon_to_tile(p.coord.lat, p.coord.lon, max_z))
        tile_key_name = '%s,%s' % (tile_str,gt_key_name)
        t = Tile.get_by_key_name(tile_key_name)
        points = json.loads(t.points_native)
        for i in range(len(points)):
            if points[i]['key_name'] == key_name:
                del(points[i])
                break
        t.points_native = json.dumps(points)
        t.put()
        #mark this tile updated and update all tiles
        gt = cls.get_by_key_name(gt_key_name)
        tiles_updated = sorted_tiles_set(gt.tiles_updated)
        tiles_updated.insert(tile_key_name)
        gt.tiles_updated = list(tiles_updated)
        #decrease points count
        gt.number_points -= 1
        gt.put()
        gt.update_tiles()
        #delete point
        p.delete()
    
    @classmethod
    def remove_from_geotree_by_key_name(cls, key_name, coord, gt_key_name=None, max_z=None):
        """this method removes mentionings of a point from geotree
        coord is GeoPtProperty
        the points itself is not changed (it may not even exist in datastore)
        """
        #delete from native tile
        if not gt_key_name:
            gt_key_name = cls._GEO_TREE_KEY
        if not max_z:
            max_z = get_max_z(gt_key_name)
        tile_str = tile_tuple_to_str(lat_lon_to_tile(coord.lat, coord.lon, max_z))
        tile_key_name = '%s,%s' % (tile_str,gt_key_name)
        logging.debug(tile_key_name)
        t = Tile.get_by_key_name(tile_key_name)
        points = json.loads(t.points_native)
        for i in range(len(points)):
            if points[i]['key_name'] == key_name:
                del(points[i])
                break
        t.points_native = json.dumps(points)
        t.put()
        #mark this tile updated and update all tiles
        gt = cls.get_by_key_name(gt_key_name)
        tiles_updated = sorted_tiles_set(gt.tiles_updated)
        tiles_updated.insert(tile_key_name)
        gt.tiles_updated = list(tiles_updated)
        #decrease points count
        gt.number_points -= 1
        gt.put()
        gt.update_tiles()
