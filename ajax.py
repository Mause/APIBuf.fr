# import hashlib
import logging
import webapp2
try:
    import json
except ImportError:
    import simplejson as json

from visual import Buffr
# from utils import is_valid_url
# from utils import get_gravatar
# from functional import render
# from functional import get_buffr_content

# from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
# from google.appengine.api import urlfetch
# from google.appengine.api import taskqueue


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('id; %s</br>' % users.get_current_user().user_id())


class DeleteHandler(webapp2.RequestHandler):
    def get(self, current_buffr_id):
        user = users.get_current_user()
        logging.info('Buffr id to delete; ' + current_buffr_id)
        if current_buffr_id:
            # delete the individual cache
            memcache.delete(current_buffr_id)
            memcache.delete('%s-buffrs' % user.user_id())

            query = Buffr.all()
            query.filter('end_point =', current_buffr_id)
            fetched = query.fetch(1)
            if len(fetched) != 0:
                fetched[0].delete()
                self.response.write(
                    json.dumps({'error': None, 'message': 'successful'}))
                logging.info(
                    'Buffr deleted')
            else:
                logging.info('Buffr not found in datastore or memcache')
                self.response.write(json.dumps({'error': 'no_such_buffr'}))
                return
        else:
            logging.info('Malformed url')
            self.response.write(json.dumps({'error': 'malformed_url'}))


app = webapp2.WSGIApplication(
    [(r'/ajax/buffr/delete/(?P<buffr_id>.*)', DeleteHandler)],
    debug=True)
