from tipfy.auth import MultiAuthStore as BaseAuthStore

class MultiAuthStore(BaseAuthStore):

    def login_url(self, **kwargs):
        return self._url('auth/signin', **kwargs)

    def logout_url(self, **kwargs):
        return self._url('auth/signout', **kwargs)

    def signup_url(self, **kwargs):
        return self._url('auth/signin', **kwargs)
    
    def get_user_entity(self, auth_id):
        """Loads an user entity from datastore. Override this to implement
        a different loading method. This method will load the user depending
        on the way the user is being authenticated: for form authentication,
        username is used; for third party or App Engine authentication,
        auth_id is used.

        :param auth_id:
            Unique authentication id.
        :returns:
            A ``User`` model instance, or None.
        """
        return self.user_model.get_by_auth_id(auth_id)

    def login_with_form(self, email, password, remember=False):
        """Authenticates the current user using data from a form.

        :param email:
            Email.
        :param password:
            Password.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            True if login was succesfull, False otherwise.
        """
        self.loaded = True
        auth_id = 'own|%s' % email
        user = self.get_user_entity(auth_id=auth_id)

        if user is not None and user.check_password(password) is True:
            # Successful login. Check if session id needs renewal.
            user.renew_session(max_age=self.config['session_max_age'])
            # Make the user available.
            self._user = user
            # Store the cookie.
            self._set_session(user.auth_id, user, remember)
            return True

        # Authentication failed.
        return False
