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
# try:
#     import json
# except ImportError:
#     import simplejson as json

from utils import is_valid_url
from utils import get_gravatar
from functional import render
from functional import get_url_content

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
# from google.appengine.api import urlfetch
# from google.appengine.ext.webapp import template


current_api_version = 0.1
how_many_buffrs_per_user = 15
user_readable_convertion_table = [
    ('30000', '30 seconds'),
    ('60000', '1 minute'),
    ('180000', '3 minutes'),
    ('300000', '5 minutes'),
    ('600000', '10 minutes'),
    ('1800000', '30 minutes'),
    ('3600000', '1 hour')]


class UserInstance(db.Model):
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
    last_known_data = db.StringProperty()
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
        buffr_instance.user_readable_update_interval = (
            filter(lambda x: x[0] == self.request.get('updateInterval'), user_readable_convertion_table)[0][1])
        # buffr_instance.end_point = hashlib.md5(buffr_instance.key()).hexdigest()  # this line will probably be updated in the future
        buffr_instance.last_known_data = None
        buffr_instance.buffr_version = current_api_version
        buffr_instance.put()  # this is so we can get a key for the next step
        buffr_instance.end_point = hashlib.md5(str(buffr_instance.key())).hexdigest()
        buffr_instance.put()
        logging.info('Added new Buffr to datastore')
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
    def get(self, current_buffr_id, wut, relative_api_url):
        logging.info('current_buffr_id = %s' % (current_buffr_id))
        logging.info('relative_url = %s' % (relative_api_url))

        if current_buffr_id:
            if not relative_api_url:
                relative_api_url = '/'
            else:
                relative_api_url = '/' + relative_api_url

            query = Buffr.all()
            query.filter('end_point =', current_buffr_id)
            if len(query.fetch(1)) != 0:
                selected_buffr = query.fetch(1)[0]

                # ensure that there is a / between the apiAddress and the relative url
                if not selected_buffr.apiAddress.endswith('/') and not relative_api_url.startswith('/'):
                    url_to_request = selected_buffr.apiAddress + '/' + relative_api_url
                else:
                    url_to_request = selected_buffr.apiAddress + relative_api_url

                # ensure that the api address has a valid protocol extension
                if url_to_request.split(':')[0] not in ['https', 'http', 'ftp']:
                    url_to_request = 'http://' + url_to_request
                logging.info('url_to_request; ' + str(url_to_request))

                self.response.write(get_url_content(selected_buffr, url_to_request, self))
            else:
                self.response.write('<!-- no such buffr -->')
                # self.error(301)
        else:
            self.response.write('<!-- malformed url -->')
            # self.error(301)


class BuffrdDataFlusherHandler(webapp2.RequestHandler):
    def get(self, buffr_id):
        self.response.write('Hey! GTFO!')


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


class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<h2>testing</h2>')
        self.response.write(self.request.get('poll_id'))

# class CurrentTimeHandler(webapp2.RequestHandler):
#     def get(self):
#         self.response.write(json.dumps({'time': (time.ctime())}))
#         (r'/cur_time.*', CurrentTimeHandler),  # this is for offline testing purposes

buffr_server_regex = (
    r'/api/v1/'                   # Match the beginning of the url
    r'(?P<buffr_id>\w{32})'       # match the md5 sum of the buffr, 32 instances of any word character
    r'($|/(?P<relative_url>.+))'  # optionally, match a relative URL of one or more chars in length.
                                  # else, match the end of the URL
    )

buffr_flusher_regex = (
    r'/api/v1/flush/'                   # Match the beginning of the url
    r'(?P<buffr_id>\w{32})'       # match the md5 sum of the buffr, 32 instances of any word character
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
        (r'/', MainHandler)
    ],
    debug=True)
