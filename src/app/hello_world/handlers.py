# -*- coding: utf-8 -*-
"""
    hello_world.handlers
    ~~~~~~~~~~~~~~~~~~~~

    Hello, World!: the simplest tipfy app.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
import logging
import os

from tipfy.app import Response
from tipfy.handler import RequestHandler
from tipfyext.jinja2 import Jinja2Mixin

from checkins.models import Checkin


class HelloWorldHandler(RequestHandler, Jinja2Mixin):
    def get(self):
        """Index page."""
        checkins = Checkin.all().order("-time")
        context = {
                'current_user': self.auth.user,
                'debug' : os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'),
                'checkins': checkins,
        }
        logging.error(self.auth.session)
        return self.render_response('index.html', **context)


class PrettyHelloWorldHandler(RequestHandler, Jinja2Mixin):
    def get(self):
        """Simply returns a rendered template with an enigmatic salutation."""
        context = {
            'message': 'Hello, World!',
        }
        return self.render_response('hello_world.html', **context)
