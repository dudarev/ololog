#!/usr/bin/python
"""
 This module implements sorted list and sorted set. Using them, particular subclasses relevant for GeoTree class are implemented:

     sorted_tiles_set - a set of strings 'x,y,z' that sorts them based on z, then on y, then on x;
     sorted_points_list_limited - a sorted list of points represented as dictionaries sorted based on item['importance'], 
     if number of items is equal to maximum possible, after insertion of a new item the list is trimmed again.
"""


__author__ = 'Artem Dudarev'
__licence__ = 'Apache'
__date__ = 'Sun 02 May 2010 02:04:35 PM EEST'


class sorted_list(list):
    """sorted list with sort function
    """

    def __init__(self,l,sort_func = cmp):
        list.__init__(self,l)
        self.sort_func = sort_func
        self.sort()

    def sort(self):
        list.sort(self,self.sort_func)

    def insert(self,item):
        """insert item in order IN PLACE"""
        # i,j - indices of two elements between each to insert
        i = 0
        j = len(self)-1

        # check for empty list
        if not self:
            list.insert(self,0,item)
            return

        if self.sort_func(self[i],item) == 0:
            j = i

        if self.sort_func(self[j],item) == 0:
            i = j

        if self.sort_func(self[i],item) > 0:
            list.insert(self,i,item)
            return

        if self.sort_func(self[j],item) < 0:
            list.insert(self,j+1,item)
            return

        while (j - i) > 1:
            mid = (i + j)//2
            c = self.sort_func(self[mid],item)
            if c == 0:
                i = mid
                j = mid
            if c < 0:
                i = mid
            else:
                j = mid

        list.insert(self,i+1,item)

    def extend(self,items):
        for i in items:
            self.insert(i)


class sorted_set(sorted_list):
    """sorted list with distinct elements, sublass of sorted_list above"""
    def __init__(self,l,sort_func = cmp):
        sorted_list.__init__(self,list(set(l)),sort_func)
        self.sort_func = sort_func

    def insert(self,item):
        """insert item in order IN PLACE
        different from sorted list, because if an item exists - do nothing"""

        # check for empty list
        if not self:
            list.insert(self,0,item)
            return

        # i,j - indices of two elements between each to insert
        i = 0
        j = len(self)-1

        if self.sort_func(self[i],item) == 0 or self.sort_func(self[j],item) == 0:
            return

        if self.sort_func(self[i],item) > 0:
            list.insert(self,i,item)
            return

        if self.sort_func(self[j],item) < 0:
            list.insert(self,j+1,item)
            return

        while (j - i) > 1:
            mid = (i + j)//2
            c = self.sort_func(self[mid],item)
            if c == 0:
                return
            if c < 0:
                i = mid
            else:
                j = mid

        list.insert(self,i+1,item)


class sorted_tiles_set(sorted_set):
    """sorted list of distinct strings in format 'x,y,z,GeoTree key name'
    string with larger z is considered 'smaller'"""

    @staticmethod
    def _get_tile_numbers(t):
        return map(int,t.split(',')[:3])

    @staticmethod
    def _cmp_tiles(t1,t2):
        """compares two strings in format 'x,y,z'
        tiles with larger z are considered 'smaller'"""

        x1,y1,z1 = sorted_tiles_set._get_tile_numbers(t1)
        x2,y2,z2 = sorted_tiles_set._get_tile_numbers(t2)

        cz = cmp(z2,z1) 
        cy = cmp(y2,y1)
        cx = cmp(x2,x1)

        if not cz == 0:
            return cz

        if not cy == 0:
            return cy

        if not cx == 0:
            return cx

        return 0

    def __init__(self,l):
        sorted_set.__init__(self,l,sort_func=sorted_tiles_set._cmp_tiles)

    def remove(self,*args):
        if isinstance(args[0],list):
            for e in args[0]:
                list.remove(self,e)
        else:
            for e in args:
                list.remove(self,e)


class sorted_points_list(sorted_list):
    """sorted list of points represented as dictionaries
    sorting is done by comparing point['importance']
    no limitation on size
    """

    @staticmethod
    def _cmp_points(p1,p2):
        "compares importance of two points, more important will come first"
        return -1*cmp(p1['importance'],p2['importance'])

    def __init__(self,l):
        sorted_list.__init__(self,l,sort_func=sorted_points_list._cmp_points)


class sorted_points_list_limited(sorted_points_list):
    """sorted list of points represented as dictionaries
    sorting is done by comparing point['importance']
    size of the list may not exceed len_max defined in __init__
    """

    def __init__(self,l,len_max=5):
        self.len_max = len_max
        if len(l) > len_max:
            l = l[:len_max]
        sorted_list.__init__(self,l,sort_func=sorted_points_list_limited._cmp_points)

    def insert(self,point):
        "returns True if inserts, False if not"
        # if list is full and last point is larger than point return False
        if len(self) == self.len_max and self._cmp_points(self[-1],point)<0:
            return False
        sorted_list.insert(self,point)
        if len(self) > self.len_max:
            self.pop()
        return True
