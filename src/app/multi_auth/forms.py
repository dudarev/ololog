from tipfy.i18n import lazy_gettext as _
from tipfyext.wtforms import Form, fields, validators
                                        
req = validators.required(message=_('This field is required'))
namesize = validators.length(min=3, max=16, message=_('User name must have between %(min)d and %(max)d characters', min=3, max=16))
passize = validators.length(min=8, max=32, message=_('Password must be at least %(min)d characters long', min=8, max=32))
emailsize = validators.length(min=5, max=200, message=_('Email must have at least %(min)d characters', min=5)) 
emailformat = validators.email(message=_('Valid email address is required'))
match = validators.equal_to('confirm', message=_('Passwords must match'))

class SignupForm(Form):
#    csrf_protection = True
    username = fields.TextField(_('User name'), [req, namesize])
    email = fields.TextField(_('Email'), [req, emailsize, emailformat])
    password = fields.PasswordField(_('New Password'), [req, passize]) # match
#    confirm  = fields.PasswordField(_('Repeat Password'), [req])

class SigninForm(Form):
#    csrf_protection = True
    email = fields.TextField(_('Email'), [req, emailsize, emailformat])
    password = fields.PasswordField(_('Password'), [req, passize])
    remember = fields.BooleanField(_('Keep me signed in')) 
