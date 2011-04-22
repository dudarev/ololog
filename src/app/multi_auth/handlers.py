# -*- coding: utf-8 -*-
import logging

from tipfy.sessions import SessionMiddleware
from tipfy.auth import login_required, user_required
from tipfy.auth.google import GoogleMixin
from tipfy.auth.twitter import TwitterMixin
from tipfy.i18n import _
from tipfy import RequestHandler

from tipfyext.jinja2 import Jinja2Mixin


class AuthHandler(RequestHandler, Jinja2Mixin):
    def get(self):
        """Let a user choose login method."""
        context = {
        }
        logging.error(self.auth.session)
        return self.render_response('auth.html', **context)


class AuthRequestHandler(RequestHandler):
    middleware = [SessionMiddleware()]
    
    def _on_auth_redirect(self):
        """Redirects after successful authentication."""
        if '_redirect' in self.session:
            url = self.session.pop('_redirect')
        else:
            url = '/'

        if not self.auth.user:
            url = self.auth.signup_url()

        return self.redirect(url)
    
    def redirect_path(self, default='/'):
        if '_redirect' in self.session:
            url = self.session.pop('_redirect')
        else:
            url = self.request.args.get('redirect', '/')
        if not url.startswith('/'):
            url = default
        return url


class LogoutHandler(AuthRequestHandler):
    def get(self, **kwargs):
        self.auth.logout()
        return self.redirect('/')


class TwitterAuthHandler(AuthRequestHandler, TwitterMixin):
    """TODO: not implemented yet"""
    def get(self):
        url = self.redirect_path()

        if self.auth.session:
            # User is already signed in, so redirect back.
            return self.redirect(url)

        self.session['_redirect'] = url

        if self.request.args.get('oauth_token', None):
            return self.get_authenticated_user(self._on_auth)

        return self.authorize_redirect()

    def _on_auth(self, user): 
        url = self.redirect_path() 
        if not user: 
            self.session_store.delete_cookie('_oauth_request_token') 
            return self.abort(403) 
        else: 
            auth_id = 'twitter|%s' % user['username'] 
            self.auth.login_with_auth_id(auth_id, True) 
            if not self.auth.user: 
                self.auth.create_user(username=user['username'], auth_id=auth_id, type='twitter') 
        return self.redirect(url) 


class GoogleAuthHandler(AuthRequestHandler, GoogleMixin):
    """Login with Google OpenID"""
    def get(self):
        url = self.redirect_path()

        if self.auth.session:
            # User is already signed in, so redirect back.
            return self.redirect(url)

        self.session['_redirect'] = url

        if self.request.args.get('openid.mode', None):
            return self.get_authenticated_user(self._on_auth)

        return self.authenticate_redirect()

    def _on_auth(self, user):
        url = self.redirect_path()
        if not user:
            self.abort(403)

        email = user.pop('email', '')
        auth_id = 'google|%s' % email
        self.auth.login_with_auth_id(auth_id, True) 

        if not self.auth.user: 
            user = self.auth.create_user(username=user['name'], auth_id=auth_id, email=email, type='google') 
        return self.redirect(url) 
