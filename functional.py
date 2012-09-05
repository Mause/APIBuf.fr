import time
import os
import hashlib
import logging
try:
    import json
except ImportError:
    import simplejson as json

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

# global online
# from visual import online


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
    # template_values["to_console"]["online"] = online
    template_values["to_console"] = json.dumps(template_values["to_console"])
    template_values["currentAddress"] = handler.request.host_url
    template_values['logged_in'] = logged_in
    template_values['appropriate_acct_url'] = appropriate_acct_url
    path = os.path.join(os.path.dirname(__file__), 'templates/' + filename)
    handler.response.out.write(template.render(path, template_values))


def get_url_content(buffr_instance, url, handler=None):
    "this is a caching function, to help keep wait time short"
    result = None
    lasttime_memcache_key = hashlib.md5(
        str(buffr_instance.key()) + "sincelasttime").hexdigest()
    lasttime = memcache.get(lasttime_memcache_key)

    url_hash = hashlib.md5(str(buffr_instance.key()) + str(url)).hexdigest()

    logging.info("lasttime: " + str(lasttime))
    if lasttime:
        logging.info("difference: " + str(time.time() - lasttime))
    if lasttime != None and (time.time() - lasttime) > 60:
        try:
        # if True:
            logging.info(
                "retrieving data from the users api; time > sixty seconds")
            result = urlfetch.fetch(url).read()
            if buffr_instance.last_known_data == None:
                pass
        except urlfetch.DownloadError:
            result = None
        memcache.set(lasttime_memcache_key, time.time(), 3600)
    if result == None:
        logging.info("result was none, trying memcache and then the users api")
        result = memcache.get(str(url_hash))
        if result != None:
            logging.info('Memcache get successful ' + str(result))
            return result
        else:
            logging.info('Getting the result from the users api')
            # try:
            if True:
                request_object = urlfetch.fetch(url)
                logging.info('URL: ' + request_object.final_url)
                url_data = request_object.content
                logging.info("url_data" + str(url_data))
                # logging.info("url_data" + str(dir(url_data))
                # memcache.set(lasttime_memcache_key, time.time(), 3600)
                result = url_data
                memcache.set(str(url_hash), result, 3600)
                return result
            # except urlfetch.DownloadError:
                # handler.error(408)
                # TODO:
                    # what does 408 mean?
                    # lets just stick with 404 for the moment
                # handler.error(404)
                # return ''
    else:
        return result
