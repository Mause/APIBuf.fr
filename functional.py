import time
import os
import logging
try:
    import json
except ImportError:
    import simplejson as json

import webapp2
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template


def render(handler, filename, template_values):
    user = users.get_current_user()
    if user:
        logged_in = True
        appropriate_acct_url = '/logout'
    else:
        logged_in = False
        appropriate_acct_url = '/login'
    if "to_console" not in template_values.keys():
        template_values["to_console"] = {}
    template_values["to_console"] = json.dumps(template_values["to_console"])
    template_values["currentAddress"] = handler.request.host_url
    template_values['logged_in'] = logged_in
    template_values['appropriate_acct_url'] = appropriate_acct_url
    path = os.path.join(os.path.dirname(__file__), 'templates/' + filename)
    handler.response.out.write(template.render(path, template_values))


def get_buffr_content(buffr_info, relative_api_url, handler=None):
    "this is a caching function, to help keep wait time short"
    # ensure URL is good
    buffr_info['instance'].apiAddress = ' '.join(
        buffr_info['instance'].apiAddress.split())

    cur_address = None
    # buffr_info['instance'].apiAddress

    retrieve_new = False

    if ('lasttime' in buffr_info and buffr_info['lasttime'] != None):
        if (time.time() - buffr_info['lasttime']) > buffr_info['instance'].update_interval:
            logging.info("%s > %s seconds. will retrieve data" % (
                time.time() - buffr_info['lasttime'],
                buffr_info['instance'].update_interval))
            retrieve_new = True
        else:
            logging.info('New data not required')
            retrieve_new = False
    else:
        logging.info('No lasttime info. Will retrieve new data')
        retrieve_new = True

    if not buffr_info['instance'].last_known_data:
        retrieve_new = True

    if retrieve_new:
        logging.info('Getting the result from the endpoint')
        try:
            request_object = urlfetch.fetch(cur_address)
        except urlfetch.InvalidURLError:
            logging.info('Bad URL; "%s"' % cur_address)
        except urlfetch.DownloadError:
            logging.info('Download error. Oh noes!')
            handler.error(408)
            return
        else:
            buffr_info['instance'].last_known_data = request_object.content
            buffr_info['lasttime'] = time.time()
            memcache.set(buffr_info['instance'].end_point, buffr_info)
            logging.info('Requested URL; %s' % ())
            logging.info(request_object.content)
            return request_object.content
    else:
        return buffr_info['instance'].last_known_data


class URLValidatorHandler(webapp2.RequestHandler):
    def post(self):
        buffr_instance = db.get(self.request.get('key'))
        url = ' '.join(buffr_instance.apiAddress.split())
        if url != buffr_instance.apiAddress:
            buffr_instance.apiAddress = url

        try:
            urlfetch.fetch(url)
        except urlfetch.DownloadError:
            logging.debug('Could not validate url.')
            return
        except urlfetch.InvalidURLError:
            logging.debug('Could not validate url.')
            return

        logging.debug('URL successfully validated')
        buffr_instance.known_as_valid = True
        buffr_instance.put()
        memcache.flush_all()


class BackendUpdateHander(webapp2.RequestHandler):
    "Is passed a Buffr Instance, and puts it into the datastore, reducing user facing latency"
    def post(self):
        pass
