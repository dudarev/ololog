#!/usr/bin/python2.5
"""This is the main file for GeoTree demo.
It includes classes for the first page and to fetch JSON data for tile.
"""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'
__date__ = 'Wed 04 Aug 2010 12:44:43 PM EEST'

import os
import logging
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache

from google.appengine.api.labs import taskqueue

from geotree.geotree import GeoTree, Point
from geotree.geomath import lat_lon_to_tile, tile_to_lat_lon

from xml.etree  import cElementTree as etree
import time, datetime

from models import OSMPOI, OSMTile

import config

from django.utils import simplejson as json


class GetTiles(webapp.RequestHandler):
    def get(self):
        center = self.request.get('c').strip()
        gt_key_name = self.request.get('gt').strip()
        if not gt_key_name:
            gt_key_name = 'osm'
        tiles = GeoTree.fetch_around_tile(center, gt_key_name=gt_key_name)
        self.response.out.write(tiles);


class UpPlace(webapp.RequestHandler):
    def get(self,key_name):
        p = OSMPOI.get_by_key_name(key_name)
        p.update_importance(p.importance+1, max_z=config.max_z_osm, gt_key_name="osm")
        taskqueue.add(url='/gt/admin/update_tiles', method='GET')
        self.response.out.write('increased importance');


class DownPlace(webapp.RequestHandler):
    def get(self,key_name):
        p = OSMPOI.get_by_key_name(key_name)
        if p.importance > 0:
            p.update_importance(p.importance-1, max_z=config.max_z_osm, gt_key_name="osm")
            taskqueue.add(url='/gt/admin/update_tiles', method='GET')
        self.response.out.write('decreased importance');


class GetPlace(webapp.RequestHandler):
    def get(self,key_name):
        p = OSMPOI.get_by_key_name(key_name)
        if p:
            self.response.out.write("attr: ")
            attrs = json.loads(p.attr)
            for a in attrs:
                self.response.out.write("<br/>&nbsp;&nbsp;")
                self.response.out.write(a)
                self.response.out.write(": ")
                self.response.out.write(attrs[a])
            self.response.out.write("<br/>tags: ")
            tags = json.loads(p.tags)
            for t in tags:
                self.response.out.write("<br/>&nbsp;&nbsp;")
                self.response.out.write(t)
                self.response.out.write(": ")
                self.response.out.write(tags[t])
        else:
            self.response.out.write("no such place");
        self.response.out.write("<br/>importance: "+str(p.importance))

def is_download_on():
    memcache_key = "download_state"
    download_state = memcache.get(memcache_key)
    if download_state is None:
        return False
    return download_state

class RequestUpdateOSM(webapp.RequestHandler):
    "add task to update OSM tiles to queue"
    def get(self):
        if is_download_on():
            ll = self.request.get('ll').strip()
            taskqueue.add(url='/gt/do_update', params={'ll': ll})
            self.response.out.write( "added task")
        else:
            self.response.out.write( "OSM download state is off")


def timedelta_to_seconds(time_delta):
    """converts datetime.timedelta to seconds"""
    return time_delta.days * 86400 + time_delta.seconds


class DoUpdateOSM(webapp.RequestHandler):
    "update 3x3 tiles around tile with zoom=17 where a point specified in ll is located"
    def MarkOSMTileUpdated(self, x, y, z):
        key_name = '%d,%d,%d' % (x, y, z)
        t = OSMTile.get_by_key_name(key_name)
        if not t:
            t = OSMTile(key_name=key_name)
        t.put()

    def isOSMTileUpdated(self, x, y, z):
        key_name = '%d,%d,%d' % (x, y, z)
        t = OSMTile.get_by_key_name(key_name)
        now = datetime.datetime.utcnow()
        if t:
            self.response.out.write( "updated %d seconds ago\n" % timedelta_to_seconds(now - t.time_fetched) )
            return True
        else:
            return False

    def post(self):
        ll = self.request.get('ll')
        lat,lon = map(float,ll.split(','))
        (x, y, z) = lat_lon_to_tile(lat, lon, config.max_z_osm)
        if self.isOSMTileUpdated(x, y, z):
            self.response.out.write( "this tile is updated" )
            return

        # OSM BBOX convention - left,bottom,right,top
        # http://wiki.openstreetmap.org/wiki/Bounding_Box
        
        top,left = tile_to_lat_lon(x-1, y-1, z)
        bottom,right = tile_to_lat_lon(x+2, y+2, z)

        url = "http://open.mapquestapi.com/xapi/api/0.6/map?bbox=%f,%f,%f,%f" % (left, bottom, right, top)
        # url = "http://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (left, bottom, right, top)
        self.response.out.write( "updating tiles %s" % (url) );

        try:
          data = urllib2.urlopen(url)
        except urllib2.URLError, e:
            self.response.out.write( "error fetching url" )
            return

        count_ways = 0
        count_ways_closed = 0
        count_ways_closed_named = 0
        names_closed_ways = []

        count_nodes_tagged = 0
        count_nodes_named = 0
        names_nodes = []

        time_format = "%Y-%m-%dT%H:%M:%SZ"

        nodes_dict = {}

        for event, elem in etree.iterparse(data):
            
            if elem.tag == 'node':
                tags = elem.findall('tag')
                id = elem.attrib['id']
                nodes_dict[id] = elem
                if tags:
                    if len(tags)==1 and tags[0].attrib['k']=='created_by':
                        continue
                    name = ''
                    importance = 1.
                    value_str = elem.attrib['timestamp']
                    time_edited_in_osm = datetime.datetime.fromtimestamp(time.mktime(time.strptime(value_str, time_format)))
                    attr = json.dumps(elem.attrib)
                    lat = elem.attrib['lat']
                    lon = elem.attrib['lon']
                    coord = "%s,%s" % (lat,lon)
                    
                    tags_dict = {}
                    for t in tags:
                        tags_dict[t.attrib['k']] = t.attrib['v']
                        if t.attrib['k'] == 'name':
                            count_nodes_named += 1
                            names_nodes.append(t.attrib['v'])
                            name = t.attrib['v']
                            importance = 3.

                    p = OSMPOI.get_by_key_name(id)
                    if p:
                        p = p
                    else:
                        p = OSMPOI(
                                key_name=id,
                                coord=coord,
                                attr=attr,
                                tags=json.dumps(tags_dict),
                                time_edited_in_osm=time_edited_in_osm,
                                name=name,
                                importance=importance
                            )
                    p.put()

                    self.response.out.write('\n%s' % elem.attrib['id'])
                    self.response.out.write('\n%s' % str(time_edited_in_osm) )
                    count_nodes_tagged += 1

            if elem.tag == 'way':
                count_ways += 1
                nds = elem.findall('nd')
                # if closed way
                if nds[0].attrib['ref'] == nds[-1].attrib['ref']:

                    count_ways_closed += 1
                    tags = elem.findall('tag')
                    if tags:
                        if len(tags)==1 and tags[0].attrib['k']=='created_by':
                            continue
                        id = 'w'+elem.attrib['id']
                        name = ''
                        importance = 2.
                        value_str = elem.attrib['timestamp']
                        time_edited_in_osm = datetime.datetime.fromtimestamp(time.mktime(time.strptime(value_str, time_format)))
                        attr = json.dumps(elem.attrib)
                        tags_dict = {}
                        for t in tags:
                            tags_dict[t.attrib['k']] = t.attrib['v']
                            if t.attrib['k'] == 'name':
                                count_ways_closed_named += 1
                                names_closed_ways.append(t.attrib['v'])
                                name = t.attrib['v']
                                importance = 4.
                        # find coordinates
                        lat = 0.
                        lon = 0.
                        # do not count last node because it repeats the first
                        for n in nds[:-1]:
                            node_id = n.attrib['ref']
                            node = nodes_dict[node_id]
                            lat += float(node.attrib['lat'])
                            lon += float(node.attrib['lon'])
                        l = len(nds) - 1.
                        lat = lat/l
                        lon = lon/l
                        coord = "%f,%f" % (lat,lon)

                        p = OSMPOI.get_by_key_name(id)
                        if p:
                            p = p
                        else:
                            p = OSMPOI(
                                    key_name=id,
                                    coord=coord,
                                    attr=attr,
                                    tags=json.dumps(tags_dict),
                                    time_edited_in_osm=time_edited_in_osm,
                                    name=name,
                                    importance=importance
                                )
                        p.put()

        # mark OSMTiles as updated
        for xx in range(x-1,x+2):
            for yy in range(y-1,y+2):
                self.MarkOSMTileUpdated(xx,yy,z)

        taskqueue.add(url='/gt/admin/add_points', method='GET')

        self.response.out.write('\nways: %d' % count_ways)
        self.response.out.write('\nclosed ways: %d' % count_ways_closed)
        self.response.out.write('\nnamed closed ways: %d' % count_ways_closed_named)
        self.response.out.write('\ntagged nodes: %d' % count_nodes_tagged)
        self.response.out.write('\nnamed nodes: %d' % count_nodes_named)

class MainHandler(webapp.RequestHandler):
    def get(self):

        path = os.path.join(os.path.dirname(__file__), 'templates/geotree_index.html')
        self.response.out.write(template.render(path,{}))


application = webapp.WSGIApplication([
                                    ('/gt', MainHandler),
                                    ('/gt/t/', GetTiles),
                                    ('/gt/p/(.*)', GetPlace),
                                    ('/gt/up/', RequestUpdateOSM),
                                    ('/gt/do_update', DoUpdateOSM),
                                    ('/gt/up_place/(.*)', UpPlace),
                                    ('/gt/down_place/(.*)', DownPlace),
                                    ],
                                   debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
