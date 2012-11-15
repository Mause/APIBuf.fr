#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import hashlib
import logging
import webapp2

from utils import is_valid_url
from utils import get_gravatar
from functional import render
from functional import URLValidatorHandler
from functional import get_buffr_content

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
# from google.appengine.api import urlfetch
from google.appengine.api import taskqueue


current_api_version = 0.1
how_many_buffrs_per_user = 15
user_readable_convertion_table = [
    ('30000', '30 seconds', '30 seconds'),
    ('60000', '1 minute', 'minute'),
    ('180000', '3 minutes', '3 minutes'),
    ('300000', '5 minutes', '5 minutes'),
    ('600000', '10 minutes', '10 minutes'),
    ('1800000', '30 minutes', '30 minutes'),
    ('3600000', '1 hour', 'hour')]


class UserInstance(db.Model):
    alpha_user = db.BooleanProperty()
    user_id = db.StringProperty()


class Buffr(db.Model):
    apiName = db.StringProperty()
    apiAddress = db.StringProperty()
    APIUnstable = db.BooleanProperty()
    user_id = db.StringProperty()
    user_email = db.EmailProperty()
    update_interval = db.IntegerProperty()
    user_readable_update_interval = db.StringProperty()
    buffr_version = db.FloatProperty()
    last_known_data = db.StringProperty(multiline=True)
    known_as_valid = db.BooleanProperty()
    end_point = db.StringProperty()


class MainHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'home.html', {})


class AddBufferHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user or 'user_id' not in dir(user):
            self.redirect(users.create_login_url('/addbuffr'))
        render(self, 'addbuffer.html', {'submitted': False,
            'updateIntervalOptions': user_readable_convertion_table})

    def post(self):
        user = users.get_current_user()
        if not user or 'user_id' not in dir(user):
            self.redirect(users.create_login_url('/addbuffr'))
        apiAddress = self.request.get('apiAddress')
        to_console = {}
        to_console["apiAddress"] = apiAddress
        to_console["is_valid_url(apiAddress)"] = (is_valid_url(apiAddress) != None)

        buffr_instance = Buffr()
        buffr_instance.apiName = self.request.get('apiName')
        buffr_instance.apiAddress = apiAddress
        APIUnstable = self.request.get('APIUnstable')
        if APIUnstable not in [True, False]:
            buffr_instance.APIUnstable = False
        else:
            buffr_instance.APIUnstable = APIUnstable
        buffr_instance.user_id = user.user_id()
        buffr_instance.user_email = user.email()
        buffr_instance.update_interval = int(self.request.get('updateInterval'))
        for possibility in user_readable_convertion_table:
            logging.info(str((possibility[0], buffr_instance.update_interval)))
            if int(possibility[0]) == buffr_instance.update_interval:
                buffr_instance.user_readable_update_interval = possibility[2]
        buffr_instance.end_point = hashlib.md5('%s:%s' % (user.user_id(), apiAddress)).hexdigest()
        buffr_instance.last_known_data = None
        buffr_instance.buffr_version = current_api_version
        buffr_instance.put()
        memcache.flush_all()
        logging.info('Added new Buffr to datastore')
        taskqueue.add(url='/confirm_working_url', params={'key': buffr_instance.key()})
        render(self, 'addbuffer.html', {'to_console': to_console,
                                        'submitted': True,
                                        'apiAddress': apiAddress})


class UserInfoHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            all_buffrs = memcache.get('%s-buffrs' % user.user_id())
            if not all_buffrs:
                all_buffrs = Buffr.all()
                all_buffrs.filter('user_id =', user.user_id())
                all_buffrs = all_buffrs.fetch(how_many_buffrs_per_user)
                memcache.set('%s-buffrs' % user.user_id(), all_buffrs)

            user_icon = get_gravatar(user.email())

            render(self, 'userinfo.html', {
                'user': users.get_current_user(),
                'gravatar': user_icon,
                'currentAddress': self.request.host_url,
                'to_console': {'gravatar': user_icon},
                'all_buffrs': all_buffrs})
        else:
            self.redirect(users.create_login_url('/user'))


# the following two classes, /login and /logout should only be used
# by the links on the webpage.
class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_logout_url("/"))


class LoginHandler(webapp2.RequestHandler):
    def get(self):
        to_goto = self.request.get('redirect', '/user')
        self.redirect(users.create_login_url(to_goto))


class BuffrdDataServerHandler(webapp2.RequestHandler):
    def get(self, current_buffr_id, relative_api_url):
        logging.info('current_buffr_id = %s' % (current_buffr_id))
        logging.info('relative_url = %s' % (relative_api_url))

        if current_buffr_id:
            if not relative_api_url:
                relative_api_url = ''
            else:
                relative_api_url = '/' + relative_api_url

            selected_buffr_info = memcache.get(current_buffr_id)
            if not selected_buffr_info:
                query = Buffr.all()
                query.filter('end_point =', current_buffr_id)
                query = query.fetch(1)
                if len(query) != 0:
                    logging.debug('Selected buffr not found in memcache, found in datastore')
                    selected_buffr_info = {}
                    selected_buffr_info['instance'] = query[0]
                else:
                    logging.debug('Could not find requested buffr in datastore or memcache')
                    self.response.write('<!-- no such buffr -->')
                    self.error(301)
                    return
            else:
                logging.debug('Selected buffr found in memcache')

            self.response.write(
                get_buffr_content(selected_buffr_info, relative_api_url, self))
        else:
            self.response.write('<!-- malformed url -->')
            self.error(301)


class BuffrdDataFlusherHandler(webapp2.RequestHandler):
    def get(self, current_buffr_id):
        user = users.get_current_user()
        memcache.delete(current_buffr_id)
        memcache.delete('%s-buffrs' % user.user_id())


class Administrator(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            render(self, 'adminpage.html', {})
        elif user:
            self.redirect('/')
        else:
            self.redirect('/login?redirect=/admin')

    def post(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            render(self, 'adminpage.html', {})
        elif user:
            self.redirect('/')
        else:
            self.redirect('/login?redirect=/admin')

buffr_server_regex = (
    r'/api/v1/'                             # Match the beginning of the url
    r'(?P<buffr_id>[^/]*)'                  # match the key of the buffr, any length of any charactor bar the forward slash
    r'(?:(?:|/)$|/(?P<relative_url>.+))'    # optionally, match a relative URL of one or more chars in length. optional forward slash
                                            # else, match the end of the URL
    )


buffr_flusher_regex = (
    r'/api/v1/flush/'           # Match the beginning of the url
    r'(?P<buffr_id>[^/]*)'      # match the key of the buffr, any length of any charactor bar the forward slash
    )


app = webapp2.WSGIApplication(
    [
        (r'/addbuffr', AddBufferHandler),
        (r'/login', LoginHandler),
        (r'/logout', LogoutHandler),
        (r'/user', UserInfoHandler),
        (r'/admin', Administrator),
        (buffr_flusher_regex, BuffrdDataFlusherHandler),
        (buffr_server_regex, BuffrdDataServerHandler),
        (r'/confirm_working_url', URLValidatorHandler),
        (r'/', MainHandler)
    ],
    debug=True)
