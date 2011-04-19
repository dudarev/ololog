import logging

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from werkzeug import check_password_hash, generate_password_hash
from tipfy.i18n import _
from tipfy.auth import create_session_id
from tipfy.utils import url_for
from tipfy import current_handler
from tipfy.appengine.auth.model import User as BaseUser
from counter.models import GeneCounter as counter

from myapp.utils.tools import rand_key, Nitrox

class User(BaseUser, Nitrox):
    # key_name = rand_key
    type = db.StringProperty(required=True, choices=set(['own', 'facebook', 'twitter', 'google']))
    confirmation_token = db.StringProperty()
    is_validated = db.BooleanProperty(default=False, required=True)

    @classmethod
    def get_by_username(cls, username):
        return cls.all().filter('username =', username).get()

    @classmethod
    def get_by_auth_id(cls, auth_id):
        link = 'key_name:for:auth_id:%s' % auth_id
        id = memcache.get(link)
        if id is not None:
            return cls.pull(id)
        user = cls.all().filter('auth_id =', auth_id).get()
        if user is not None:
            memcache.set(link, user.id)
        else:
            memcache.delete(link)
        return user

    @classmethod
    def create(cls, username, auth_id, **data):
        data['key_name'] = rand_key(22)
        data['username'] = username
        data['auth_id'] = auth_id
        # Generate an initial session id.
        data['session_id'] = create_session_id()
        data['confirmation_token'] = rand_key(22)

        if 'password_hash' in data:
            # Password is already hashed.
            data['password'] = data.pop('password_hash')
        elif 'password' in data:
            # Password is not hashed: generate a hash.
            data['password'] = generate_password_hash(data['password'])

        if cls.get_by_auth_id(auth_id) is not None:
            return None
        return cls._create(data)

    def update(self, data):
        self._update(data)

    @property
    def confirm_url(self):
        if self.is_temp: return None
        return url_for('confirm', self.id, self.confirmation_token)

    def send_email(self, subject, body):
        taskqueue.add(
            queue_name='email',
            url=current_handler.url_for('system/email'),
            params={
                'to_email': self.email,
                'name': self.username,
                'subject': subject,
                'body': body,
            },
            method='POST',
        )

    def __unicode__(self):
        return unicode(self.username)
