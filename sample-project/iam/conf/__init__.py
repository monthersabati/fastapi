import os

APP_NAME = os.getenv('APP_NAME', 'IAM')
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
APP_PORT = int(os.getenv('APP_PORT', 8081))
WORKERS = int(os.getenv('WORKERS', 1))
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
WEBROOT = os.getenv('WEBROOT', '/api')

OPENSTACK_KEYSTONE_URL = os.getenv('OPENSTACK_KEYSTONE_URL', 'http://192.168.19.100:5000/v3')
OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = os.getenv('OPENSTACK_KEYSTONE_DEFAULT_DOMAIN', 'default')
OPENSTACK_SSL_NO_VERIFY = os.getenv('OPENSTACK_SSL_NO_VERIFY', 'True').lower() in ('true', '1', 'yes')
OPENSTACK_SSL_CACERT = os.getenv('OPENSTACK_SSL_CACERT', 'False').lower() in ('true', '1', 'yes')
OPENSTACK_ENDPOINT_TYPE = os.getenv('OPENSTACK_ENDPOINT_TYPE', 'public')
OPENSTACK_OWNER_ROLE = os.getenv('OPENSTACK_OWNER_ROLE', 'owner')

AUTHENTICATION_HEADER = os.getenv('AUTHENTICATION_HEADER', 'X-Authentication')
IDENTITY_HEADER = os.getenv('IDENTITY_HEADER', 'X-Identity')
