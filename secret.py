from os import urandom
from base64 import b64encode

key = urandom(64)
SECRET_KEY = b64encode(key).decode('utf-8')
