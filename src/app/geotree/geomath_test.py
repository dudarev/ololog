#!/usr/bin/python2.5

"""Unit tests for geomath.py"""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache 2.0'
__date__ = 'Sun 02 May 2010 02:26:53 PM EEST'

import unittest

from geotree import Point
import geomath


class GeomathTests(unittest.TestCase):
    def test_lat_lon_to_tile(self):
        """testing convertion of a point to tile
        
        to come up with test cases refer to
        http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/"""

        lat = 48
        lon = 37.7
        z = 10

        tile_calculated = geomath.lat_lon_to_tile(lat,lon,z)
        tile_known = (619,355,10)

        # make sure the tiles are the same
        self.assertEqual(tile_calculated,tile_known)

    def test_tile_children(self):
        x,y,z = (619,355,10)

        children_calculated = geomath.tile_children(x,y,z)
        children_known = ( (1238,710,11),
                           (1238,711,11),
                           (1239,710,11),
                           (1239,711,11))

        self.assertTrue(len(children_calculated) == 4)
        for c in children_known:
            self.assertTrue(c in children_calculated)

    def test_tile_children_str_with_no_extra(self):
        tile = '619,355,10'

        children_calculated = geomath.tile_children(tile)
        children_known = ( (1238,710,11),
                           (1238,711,11),
                           (1239,710,11),
                           (1239,711,11))

        self.assertTrue(len(children_calculated) == 4)
        for c in children_known:
            self.assertTrue(c in children_calculated)

        # test when return_str = True
        children_calculated_str = geomath.tile_children(tile,return_str=True)
        children_known_str = ( '1238,710,11',
                               '1238,711,11',
                               '1239,710,11',
                               '1239,711,11')

        self.assertTrue(len(children_calculated_str) == 4)
        for c in children_known_str:
            self.assertTrue(c in children_calculated_str)

    def test_tile_children_str(self):
        tile = '619,355,10,a'

        children_calculated = geomath.tile_children(tile)
        children_known = ( (1238,710,11),
                           (1238,711,11),
                           (1239,710,11),
                           (1239,711,11))

        self.assertTrue(len(children_calculated) == 4)
        for c in children_known:
            self.assertTrue(c in children_calculated)

        # test when return_str = True
        children_calculated_str = geomath.tile_children(tile,return_str=True)
        children_known_str = ( '1238,710,11,a',
                               '1238,711,11,a',
                               '1239,710,11,a',
                               '1239,711,11,a')

        self.assertTrue(len(children_calculated_str) == 4)
        for c in children_known_str:
            self.assertTrue(c in children_calculated_str)

    def test_tile_parent(self):
        x,y,z = (619,355,10)

        parent_calculated = geomath.tile_parent(x,y,z)
        parent_known = (309,177,9)

        self.assertEqual(parent_known,parent_calculated)

    def test_tile_parent_str_with_no_extra(self):
        tile = '619,355,10'

        parent_calculated = geomath.tile_parent(tile)
        parent_known = (309,177,9)

        self.assertEqual(parent_known,parent_calculated)
       
        # same with unicode
        tile = u'619,355,10'
        parent_calculated = geomath.tile_parent(tile)
        self.assertEqual(parent_known,parent_calculated)

        # test that returns string
        parent_known_str = '309,177,9'
        parent_calculated_str = geomath.tile_parent(tile,return_str=True)
        self.assertEqual(parent_known_str,parent_calculated_str)

    def test_tile_parent_str(self):
        tile = '619,355,10,a'

        parent_calculated = geomath.tile_parent(tile)
        parent_known = (309,177,9)

        self.assertEqual(parent_known,parent_calculated)
       
        # same with unicode
        tile = u'619,355,10,a'
        parent_calculated = geomath.tile_parent(tile)
        self.assertEqual(parent_known,parent_calculated)

        # test that returns string
        parent_known_str = '309,177,9,a'
        parent_calculated_str = geomath.tile_parent(tile,return_str=True)
        self.assertEqual(parent_known_str,parent_calculated_str)

    def test_tile_str_to_tuple(self):
        s = '2,3,4,a'
        t = (2,3,4)
        self.assertEqual(t,geomath.tile_str_to_tuple(s))

    def test_tile_tuple_to_str(self):
        s = '2,3,4'
        t = (2,3,4)
        self.assertEqual(s,geomath.tile_tuple_to_str(t))


if __name__ == '__main__':
  unittest.main()
