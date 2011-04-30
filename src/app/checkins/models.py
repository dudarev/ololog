import logging

from google.appengine.ext import db
from tipfy.appengine.auth.model import User

class Info(db.Expando):
    time_added = db.DateTimeProperty(auto_now=True)

class Location(db.Expando):
    time_added = db.DateTimeProperty(auto_now_add=True)


class Checkin(db.Expando):
    time = db.DateTimeProperty(auto_now_add=True)
    location = db.ReferenceProperty(Location, collection_name='locations')
    user = db.ReferenceProperty(User, collection_name='users')
