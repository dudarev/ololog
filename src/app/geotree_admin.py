# -*- coding: utf8 -*-
"""This is for a simple login page for GeoTree demo.
The admin page requires administrator credentials (set in app.yaml).
(For localhost this separation may be not necessary.)
"""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'
__date__ = 'Sat 04 Dec 2010 03:19:58 PM EET'

from django.utils import simplejson as json
import logging

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.labs import taskqueue

from geotree.geotree import GeoTree
from models import OSMPOI, City

import config

def is_download_on():
    memcache_key = "download_state"
    download_state = memcache.get(memcache_key)
    if download_state is None:
        return False
    return download_state

def turn_download_on():
    memcache_key = "download_state"
    download_state = memcache.get(memcache_key)
    memcache.set(memcache_key, True)

def turn_download_off():
    memcache_key = "download_state"
    download_state = memcache.get(memcache_key)
    memcache.set(memcache_key, False)


class AdminHandler(webapp.RequestHandler):

    # number of points to add to db
    _BATCH_ADD_SIZE = 50
    # how many tiles are updated per update call
    _BATCH_UPDATE_SIZE = 10
    
    def get(self,action=None):
        if action:
            if action == 'turn_download_on':
                turn_download_on()
            if action == 'turn_download_off':
                turn_download_off()

        self.response.out.write('Admin page<br/><br/>')
        self.response.out.write('<a href="/gt/">Home</a><br/><br/>')
        self.response.out.write('<a href="/gt/admin/create_geo_trees">Create GeoTrees</a><br/><br/>')
        self.response.out.write('<a href="/_ah/admin">App Engine localhost admin</a><br/><br/>')
        self.response.out.write('<a href="/gt/admin/add_points">Add OSM points to GeoTree</a><br/>')
        self.response.out.write('<a href="/gt/admin/add_cities">Add cities to GeoTree</a><br/><br/>')
        self.response.out.write('<a href="/gt/admin/update_tiles">Update OSM GeoTree tiles</a><br/>')
        self.response.out.write('<a href="/gt/admin/update_cities_tiles">Update Cities GeoTree tiles</a><br/><br/>')
        if is_download_on():
            self.response.out.write('<a href="/gt/admin/turn_download_off">Turn OSM Download OFF</a><br/><br/>')
        else:
            self.response.out.write('<a href="/gt/admin/turn_download_on">Turn OSM Download ON</a><br/><br/>')

        if action:
            if action == 'create_geo_trees':
                gt = GeoTree.get(gt_key_name='osm')
                if not gt:
                    gt = GeoTree(key_name='osm', max_z=config.max_z_osm, min_z=config.min_z_osm)
                    gt.put()
                    self.response.out.write('\n\nInfo: Created osm GeoTree.')
                else:
                    gt.max_z = config.max_z_osm
                    gt.min_z = config.min_z_osm
                    gt.put()
                    self.response.out.write('\n\nInfo: OSM GeoTree exists.')
                gt = GeoTree.get(gt_key_name='cities')
                if not gt:
                    gt = GeoTree(key_name='cities', max_z=config.max_z_cities, min_z=config.min_z_cities)
                    gt.put()
                    self.response.out.write('\nInfo: Created cities GeoTree.')
                else:
                    gt.max_z = config.max_z_cities
                    gt.min_z = config.min_z_cities
                    gt.put()
                    self.response.out.write('\nInfo: Cities GeoTree exists.')
            if action == 'add_points':
                batch = OSMPOI.all().filter('is_in_tree =',False).fetch(self._BATCH_ADD_SIZE)
                if batch:
                    GeoTree.insert_points_list(batch, max_z=17, gt_key_name="osm")
                    self.response.out.write('\n\nInfo: added %d points' % len(batch))
                    for p in batch:
                        p.is_in_tree = True
                    db.put(batch)
                    taskqueue.add(url='/gt/admin/add_points', method='GET')
                else:
                    if GeoTree.exists(gt_key_name="osm"):
                        self.response.out.write('\n\nInfo: no POIs to add.')
                        taskqueue.add(url='/gt/admin/update_tiles', method='GET')
                    else:
                        self.response.out.write('\n\nInfo: GeoTree does not exist.')
            if action == 'add_cities':
                batch = City.all().filter('is_in_tree =',False).fetch(self._BATCH_ADD_SIZE)
                if batch:
                    GeoTree.insert_points_list(batch, gt_key_name="cities")
                    self.response.out.write('\n\nInfo: added %d cities' % len(batch))
                    for p in batch:
                        p.is_in_tree = True
                    db.put(batch)
                else:
                    if GeoTree.exists(gt_key_name="cities"):
                        self.response.out.write('\n\nInfo: no cities left out of tree')
                    else:
                        self.response.out.write('\n\nInfo: GeoTree does not exist')
            if action == 'update_tiles':
                message = GeoTree.update_tiles(count=self._BATCH_UPDATE_SIZE, gt_key_name="osm")
                if message:
                    if 'nothing to update' in message:
                        self.response.out.write('<br/>'+message)
                else:
                    taskqueue.add(url='/gt/admin/update_tiles', method='GET')
            if action == 'update_cities_tiles':
                message = GeoTree.update_tiles(count=self._BATCH_UPDATE_SIZE, gt_key_name="cities")
                if message:
                    self.response.out.write('<br/>'+message)
                else:
                    self.response.out.write('\n\nInfo: updated tiles')
            # memcaching is not used at the moment
            if action == 'clear_cache':
                memcache.flush_all()
                self.response.out.write('<br/>All memcache entries are deleted.')
    
    
logging.getLogger().setLevel(logging.DEBUG)
application = webapp.WSGIApplication([
                                    ('/gt/admin', AdminHandler),
                                    ('/gt/admin/(.*)', AdminHandler),
                                    ],
                                   debug=True)
                                   # debug=False)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
