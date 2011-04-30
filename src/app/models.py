#!/usr/bin/python2.5
"""Models for GeoTree Demo."""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'
__date__ = 'Mon 15 Mar 2010 10:03:46 AM EET'

from google.appengine.ext import db

from geotree.geotree import Point 

from tipfy.appengine.auth.model import User

class City(Point):
    """The City is derived from Point model in geotree.geotree
    Initially cities are loaded with bulkloader and not added to the GeoTree.
    is_in_tree 
    property is to go through all of them and add to the GeoTree.
    """
    is_in_tree = db.BooleanProperty(default=False)


class OSMPOI(Point):
    """
    """
    attr = db.TextProperty()
    tags = db.TextProperty()
    time_edited_in_osm = db.DateTimeProperty()
    time_added = db.DateTimeProperty(auto_now_add=True)
    is_in_tree = db.BooleanProperty(default=False)


class OSMTile(db.Model):
    """To keep track of tiles that were fetched from OSM.
    key_name = 'x,y,z'
    """
    time_fetched = db.DateTimeProperty(auto_now=True)
