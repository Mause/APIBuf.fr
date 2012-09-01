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
import webapp2
import time
import os
import hashlib
import logging
# import datetime
try:
    import json
except ImportError:
    import simplejson as json

from utils import is_valid_url

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template


current_api_version = 0.1
how_many_buffrs_per_user = 15
user_readable_convertion_table = {
    '30000':      '30 seconds',
    '60000':      '1 minute',
    '180000':     '3 minutes',
    '300000':     '5 minutes',
    '600000':     '10 minutes',
    '1800000':    '30 minutes',
    '3600000':    '1 hour'}


class UserInstance(db.Model):
    user_id = db.StringProperty()


class Buffr(db.Model):
    apiAddress = db.StringProperty()
    APIUnstable = db.BooleanProperty()
    user_id = db.StringProperty()
    update_interval = db.IntegerProperty()
    user_readable_update_interval = db.StringProperty()
    buffr_version = db.FloatProperty()
    # end_point = db.StringProperty()


class MainHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'home.html', {})


class AddBufferHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'addbuffer.html', {'submitted': False,
            'updateIntervalOptions': user_readable_convertion_table})

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/login')
        apiAddress = self.request.get('apiAddress')
        to_console = []
        to_console.append(apiAddress)
        to_console.append(is_valid_url(apiAddress) != None)

        buffr_instance = Buffr()
        buffr_instance.apiAddress = apiAddress
        APIUnstable = self.request.get('APIUnstable')
        if APIUnstable not in [True, False]:
            buffr_instance.APIUnstable = False
        else:
            buffr_instance.APIUnstable = APIUnstable
        buffr_instance.user_id = user.user_id()
        buffr_instance.update_interval = int(self.request.get('updateInterval'))
        buffr_instance.user_readable_update_interval = (
            user_readable_convertion_table[self.request.get('updateInterval')])
        # buffr_instance.end_point = buffr_instance.Key()
        buffr_instance.buffr_version = current_api_version
        buffr_instance.put()
        logging.info('Added new Buffr to datastore')
        render(self, 'addbuffer.html', {'to_console': json.dumps(to_console),
                                        'submitted': True,
                                        'apiAddress': apiAddress})


class UserInfoHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        # if user:
        #     query = db.GqlQuery("SELECT * FROM UserInstance WHERE user_id = :1", user.user_id())
        #     userprefs = query.get()
        # else:
        #     self.redirect('/login')
        # if userprefs != None and len(userprefs) == 0:
        if True:
            all_buffrs = Buffr.all()
            all_buffrs.filter('user_id =', user.user_id())
            all_buffrs = all_buffrs.fetch(how_many_buffrs_per_user)
            # self.response.write(all_buffrs)

        render(self, 'userinfo.html', {
            'user': users.get_current_user(),
            # 'userprefs': userprefs,
            'currentAddress': self.request.host_url,
            'all_buffrs': all_buffrs})


class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_logout_url("/"))


class LoginHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect(users.create_login_url("/"))


def render(handler, filename, template_values):
    user = users.get_current_user()
    if user:
        logged_in = True
        appropriate_acct_url = '/logout'
    else:
        logged_in = False
        appropriate_acct_url = '/login'
    template_values["currentAddress"] = handler.request.host_url
    template_values['logged_in'] = logged_in
    template_values['appropriate_acct_url'] = appropriate_acct_url
    path = os.path.join(os.path.dirname(__file__), 'templates/' + filename)
    handler.response.out.write(template.render(path, template_values))


def get_url_content(url):
    "this is a caching function, to help keep wait time short"
    result = None
    lasttime = memcache.get("sincelasttime")

    url_hash = hashlib.md5(str(url)).hexdigest()

    logging.info("lasttime: " + str(lasttime))
    if lasttime:
        logging.info("difference: " + str(time.time() - lasttime))
    if lasttime != None and (time.time() - lasttime) > 60:
        # try:
        if True:
            logging.info(
                "retrieving data from the events server; time > sixty seconds")
            result = urlfetch.fetch(url).read()
        # except urllib2.URLError, e:
        #     result = None
        memcache.set("sincelasttime", time.time(), 3600)
    if result == None:
        logging.info("result was none, trying memcache and then the RFLAN api")
        result = memcache.get(str(url_hash))
        if result != None:
            logging.info('Memcache get successful ' + str(result))
            return result
        else:
            logging.info('Getting the result from the RFLAN api')
            # try:
            if True:
#               HTTPRequest request = new HTTPRequest(
    # fetchurl, HTTPMethod.POST);
#               request.getFetchOptions().setDeadline(10d);
                logging.info('URL: ' + url)
                url_data = urlfetch.fetch(url).content
                logging.info("url_data" + str(url_data))
                # logging.info("url_data" + str(dir(url_data))
                # url_data.getFetchOptions().setDeadline(15)
                # memcache.set("sincelasttime", time.time(), 3600)
            # except:# urllib2.URLError
            #     handler.error(408)
            result = url_data
            memcache.set(str(url_hash), result, 3600)
            return result
    else:
        return result


class BuffrdDataServerHandler(webapp2.RequestHandler):
    def get(self):
        api_path = 'api/v1'
        path_data = (self.request.path).split('/')
        path_data = [x for x in path_data if x != '']
        if path_data[0:2] == api_path.split('/'):
            path_data = path_data[2:]
        current_buffr_id = path_data[0]
        relative_api_url = '/'.join(path_data[1:])

        try:
            selected_buffr = Buffr.get(current_buffr_id)
            if selected_buffr:
                url_to_request = selected_buffr.apiAddress + '/' + relative_api_url

                if url_to_request.split(':')[0] not in ['https', 'http', 'ftp']:
                    url_to_request = 'http://' + url_to_request
                logging.info('url_to_request; ' + str(url_to_request))

                self.response.write(str(self.request.path_info_peek()))
                self.response.write(get_url_content(url_to_request))
            else:
                self.error(301)
        except db.BadKeyError:
            self.error(301)


app = webapp2.WSGIApplication(
    [
        ('/addbuffr', AddBufferHandler),
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/user', UserInfoHandler),
        # ('/api/v1/([^/]+)?', BuffrdDataServerHandler),
        ('/api/v1/.*', BuffrdDataServerHandler),
        # ('/api/v1/', rest.Dispatcher),
        ('/', MainHandler)
    ],
    debug=True)
