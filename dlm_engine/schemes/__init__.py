import os

from yaml import load

with open('{0}/../static/swagger.yaml'.format(os.path.dirname(__file__)), 'r') as scheme_source:
    schemes = load(scheme_source)

AUTHENTICATE_CREATE = schemes['definitions']['Authenticate_POST']

CREDENTIALS_CREATE = schemes['definitions']['Common_Credential_POST']

LOCKS_DELETE = schemes['definitions']['Lock_DELETE']
LOCKS_CREATE = schemes['definitions']['Lock_POST']

PERMISSIONS_CREATE = schemes['definitions']['Permission_POST']
PERMISSIONS_UPDATE = schemes['definitions']['Permission_PUT']

USERS_CREATE = schemes['definitions']['User_POST']
USERS_UPDATE = schemes['definitions']['User_PUT']
