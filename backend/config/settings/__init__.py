from decouple import config

env = config('DJANGO_ENV', default='development')

if env == 'production':
    from .production import * 
elif env == 'testing':
    from .testing import *
else:
    from .development import *
    