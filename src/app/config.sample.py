# -*- coding: utf-8 -*-
"""App configuration."""
config = {}

config['tipfy'] = {'auth_store_class': 'tipfy.auth.MultiAuthStore',}

config['tipfy.sessions'] = {
       'secret_key': 'YOURSHERE',
}

config['tipfy.auth.twitter'] = {
    'consumer_key':    'YOURSHERE',
    'consumer_secret': 'YOURSHERE',
}
