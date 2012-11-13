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


def get_buffr_content(buffr_instance, url, handler=None):
    "this is a caching function, to help keep wait time short"
    # ensure URL is good
    url = ' '.join(url.split())
    result = None
    lasttime_memcache_key = hashlib.md5(
        str(buffr_instance.key()) + ":sincelasttime").hexdigest()
    lasttime = memcache.get(lasttime_memcache_key)
    url_hash = hashlib.md5('%s%s' % (buffr_instance.key(), url)).hexdigest()

    logging.info("lasttime: " + str(lasttime))
    if lasttime:
        logging.info("difference: " + str(time.time() - lasttime))
    if lasttime != None and (time.time() - lasttime) > buffr_instance.update_interval:
        try:
            logging.info(
                "retrieving data from the users api; time > %s seconds" % buffr_instance.update_interval)
            result = urlfetch.fetch(url).read()
            if buffr_instance.last_known_data == None:
                # TODO: implement unstable API handling here
                pass
        except urlfetch.DownloadError:
            logging.info('Download error. Oh noes!')
            result = None
        memcache.set(lasttime_memcache_key, time.time())
    if not result:
        logging.info("result was none, trying memcache and then the datastore")
        result = memcache.get(str(url_hash))
        if result:
            logging.info('Memcache get successful')
            return result
        else:
            logging.info('Getting the result from the datastore')
            try:
            # if True:
                request_object = urlfetch.fetch(url)
            except urlfetch.InvalidURLError:
                logging.info('Bad URL; "%s"' % url)
            except urlfetch.DownloadError:
                handler.error(408)
                # TODO:
                #    what does 408 mean?
                #    lets just stick with 404 for the moment
                # handler.error(404)
                return
            else:
                logging.info('URL: %s' % request_object.final_url)
                # logging.info("url_data" + str(request_object.content))
                # logging.info("url_data" + str(dir(url_data))
                memcache.set(lasttime_memcache_key, time.time())
                memcache.set(str(url_hash), request_object.content)
                return request_object.content
    else:
        return result
