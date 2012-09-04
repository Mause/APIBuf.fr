# import code for encoding urls and generating md5 hashes
import urllib
import hashlib


def get_gravatar(email, size=80, default="/images/default_user_80.png"):
    gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d': default, 's': str(size)})
    return gravatar_url
