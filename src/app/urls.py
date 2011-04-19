# -*- coding: utf-8 -*-
"""URL definitions."""
from tipfy.routing import Rule

rules = [
    Rule('/', name='hello-world', handler='hello_world.handlers.HelloWorldHandler'),
    Rule('/pretty', name='hello-world-pretty', handler='hello_world.handlers.PrettyHelloWorldHandler'),

    Rule('/auth', name='auth', handler='multi_auth.handlers.AuthHandler'),
    Rule('/auth/logout', name='auth-logout', handler='multi_auth.handlers.LogoutHandler'),
    Rule('/auth/google', name='auth-google', handler='multi_auth.handlers.GoogleAuthHandler'),
    Rule('/auth/twitter', name='auth-twitter', handler='multi_auth.handlers.TwitterAuthHandler'),
]
