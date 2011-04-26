#!/usr/bin/python2.5

"""Unit tests for sorted_lists.py"""

__author__ = 'Artem Dudarev'
__licence__ = 'Apache'
__data__ = 'Fri 12 Mar 2010 06:42:35 PM EET'

import unittest

from sorted_lists import sorted_list, sorted_set, sorted_tiles_set, sorted_points_list, sorted_points_list_limited


class SortedListTest(unittest.TestCase):
    def setUp(self):
        self.normal_list = [2,2,4,1,3,5,2,0,9]
    
    def test_initialization(self):
        """test that initializes and sorts"""
        l = sorted_list(self.normal_list)
        self.assertEqual(len(l),len(self.normal_list))

        # in order
        for i in range(len(l)-1):
            self.assertTrue(l[i]<=l[i+1])
    
    def test_sort_func(self):
        """specify different sort function 
        sort in reverse order"""
        l = sorted_list(self.normal_list,sort_func=lambda x,y: -1*cmp(x,y))
        # in reverse order
        for i in range(len(l)-1):
            self.assertTrue(l[i]>=l[i+1])
    
    def test_insertion(self):
        l = sorted_list(self.normal_list)
        l.insert(5)
        l.insert(2)
        self.assertEqual(len(l)-2,len(self.normal_list))
        # in reverse order
        l = sorted_list(self.normal_list,sort_func=lambda x,y: -1*cmp(x,y))
        l.insert(5)
        l.insert(2)
        self.assertEqual(len(l)-2,len(self.normal_list))
        for i in range(len(l)-1):
            self.assertTrue(l[i]>=l[i+1])
    
    def test_extension(self):
        l = sorted_list(self.normal_list)
        l.extend([1,2,3,4])
        self.assertEqual(len(l)-4,len(self.normal_list))
        self.assertTrue(4 in l)

    def test_insert_to_empty(self):
        l = sorted_list([])
        l.insert(3)
        self.assertTrue(3 in l)


class SortedSetTest(unittest.TestCase):
    def setUp(self):
        self.normal_list = [2,2,4,1,3,5,2,0,9]
    
    def test_initialization(self):
        """test that initializes and sorts"""
        l = sorted_set(self.normal_list)
        self.assertEqual(len(l),len(set(self.normal_list)))

        # in order
        for i in range(len(l)-1):
            self.assertTrue(l[i]<=l[i+1])
    
    def test_sort_func(self):
        """specify different sort function 
        sort in reverse order"""
        l = sorted_set(self.normal_list,sort_func=lambda x,y: -1*cmp(x,y))
        # in reverse order
        for i in range(len(l)-1):
            self.assertTrue(l[i]>=l[i+1])
    
    def test_insertion(self):
        l = sorted_set(self.normal_list)
        # insert existing
        existing = self.normal_list[0]
        l.insert(existing) 
        self.assertEqual(len(l),len(set(self.normal_list)))
        l.insert(50)
        l.insert(20)
        self.assertEqual(len(l)-2,len(set(self.normal_list)))
        # in reverse order
        l = sorted_set(self.normal_list,sort_func=lambda x,y: -1*cmp(x,y))
        l.insert(50)
        l.insert(20)
        self.assertEqual(len(l)-2,len(set(self.normal_list)))
        for i in range(len(l)-1):
            self.assertTrue(l[i]>=l[i+1])
    
    def test_extension(self):
        l = sorted_set(self.normal_list)
        l.extend([10,20,30,40])
        self.assertEqual(len(l)-4,len(set(self.normal_list)))
        self.assertTrue(40 in l)
        # extend with existing
        l.extend([10,20,30,40])
        self.assertEqual(len(l)-4,len(set(self.normal_list)))

    def test_insert_to_empty(self):
        l = sorted_set([])
        l.insert(3)
        self.assertTrue(3 in l)


class SortedTilesSetTest(unittest.TestCase):
    def setUp(self):
        self.normal_list = ['0,0,2,a','1,2,3,a','1,2,3,a','2,2,3,a','1,1,3,a','2,2,3,a','1,1,2,a']

    def test_initialization(self):
        """test that sorted set is initialized
        """
       
        l = sorted_tiles_set(self.normal_list)

        # no repeated tiles
        self.assertEqual(len(l),5)

        # tiles with large z are earlier
        zs = [int(s.split(',')[:3][-1]) for s in l]
        for i in range(len(zs)-1):
            self.assertTrue(zs[i]>=zs[i+1])

    def test_insertion(self):
        l = sorted_tiles_set(self.normal_list)

        # insert existing tile
        l.insert('0,0,2')
        self.assertEqual(len(l),5)

        # insert another existing tile in the middle
        l.insert('1,2,3')
        self.assertEqual(len(l),5)

        # insert nonexistent tile in the beginning
        l.insert('1,2,4')
        self.assertEqual(len(l),6)

        # insert nonexistent tile at the end
        l.insert('0,0,1')
        self.assertEqual(len(l),7)

        # insert nonexistent tile in the middle
        l.insert('1,0,3')
        self.assertEqual(len(l),8)

        # check that remains sorted
        # tiles with large z are earlier
        zs = [int(s.split(',')[:3][-1]) for s in l]
        for i in range(len(zs)-1):
            self.assertTrue(zs[i]>=zs[i+1])
    
    def test_extension(self):
        l = sorted_tiles_set(self.normal_list)

        # extend by the same list
        l.extend(l)
        self.assertEqual(len(l),5)

        # extend by list with nonexistent tiles
        l.extend(['1,2,2','0,0,3'])
        self.assertEqual(len(l),7)
    
        # extend by one existing and one not tiles
        l.extend(['2,2,2','0,0,3'])
        self.assertEqual(len(l),8)
    
        self.assertTrue('2,2,2' in l)
    
    def test_removal(self):
        l = sorted_tiles_set(self.normal_list)
        len_initial = len(l)
        l.remove(['0,0,2,a','1,2,3,a'])
        self.assertFalse('0,0,2,a' in l)
        self.assertFalse('1,2,3,a' in l)
        self.assertTrue(len(l)==len_initial-2)
        l.remove('2,2,3,a')
        self.assertTrue(len(l)==len_initial-3)


class SortedPointsList(unittest.TestCase):
    def setUp(self):
        self.normal_list = [{'importance':234},{'importance':1234},{'importance':324},{'importance':234324},{'importance':323424}]

    def test_initialization(self):
        """test that sorted list is initialized
        """
       
        l = sorted_points_list(self.normal_list)

        # points with larger importance are earlier
        zs = [x['importance'] for x in l]
        for i in range(len(zs)-1):
            self.assertTrue(zs[i]>=zs[i+1])

    def test_insertion(self):
        "test insertions"

        l = sorted_points_list(self.normal_list)
        len_init = len(l)

        # inserting more important point
        p = {'importance':1234567}
        l.insert(p)
        self.assertEqual(len(l),len_init+1)
        self.assertTrue(p in l)

        # inserting non-important point
        p = {'importance':1}
        l.insert(p)
        self.assertEqual(len(l),len_init+2)
        self.assertTrue(p in l)


class SortedPointsListLimited(unittest.TestCase):
    def setUp(self):
        self.normal_list = [{'importance':234},{'importance':1234},{'importance':324},{'importance':234324},{'importance':323424}]

    def test_initialization(self):
        """test that sorted list is initialized
        """
       
        l = sorted_points_list_limited(self.normal_list)

        # points with larger importance are earlier
        zs = [x['importance'] for x in l]
        for i in range(len(zs)-1):
            self.assertTrue(zs[i]>=zs[i+1])

        #test that maximum length is not exceeded during initialization
        len_max = 4
        l = sorted_points_list_limited(self.normal_list,len_max = len_max)
        self.assertEqual(len(l),len_max)

    def test_insertion(self):
        "test insertions"

        len_max = 4
        l = sorted_points_list_limited(self.normal_list,len_max = len_max)

        # inserting more important point
        p = {'importance':1234567}
        l.insert(p)
        self.assertEqual(len(l),len_max)
        self.assertTrue(p in l)

        # inserting non-important point
        p = {'importance':1}
        l.insert(p)
        self.assertEqual(len(l),len_max)
        self.assertFalse(p in l)
    
        # test that returns True if inserts and False otherwise
        l = sorted_points_list_limited(self.normal_list,len_max = len_max)
        p = {'importance':1234567}
        self.assertTrue(l.insert(p))
    
        p = {'importance':1}
        self.assertFalse(l.insert(p))


if __name__ == '__main__':
  unittest.main()
