# -*- coding: utf-8 -*-

import logging

from tipfy.app import Response
from tipfy.handler import RequestHandler

from models import Location, Checkin
from tipfy.appengine.auth.model import User 

from geotree.models import OSMPOI


class AddHandler(RequestHandler):
    def post(self):
        logging.error(dir(self.auth))
        if not self.auth.user:
            return Response('Error: authenticate first')
        place_key_name = self.request.form.get('place_key_name')
        l = Location.all().filter('osm =', place_key_name).fetch(1)
        if not l:
            l = Location(osm = place_key_name)
            l.put()
        else:
            l = l[0]
        c = Checkin(user=self.auth.user, location=l)
        osmpoi = OSMPOI.get_by_key_name(place_key_name)
        place_name = osmpoi.name
        if place_name:
            c.place_name = place_name
        else:
            c.place_key_name = osmpoi.key().name()
        c.user_name = self.auth.user.username
        c.put()
        return Response('Success %s, %s' % (self.auth.user, place_key_name) )

    def get(self):
        return Response('OK')
