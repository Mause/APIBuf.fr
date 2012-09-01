"""A toy-level example of a data model in Google Appengine DB terms.
"""
import logging
from google.appengine.ext import db
import restutil


class Doctor(db.Model):
  """Models a doctor (who might be carrying a pager).

  Attributes:
    name: the doctor's full name
    pager_set: rev-ref to set of pagers (implicitly built later)
  """
  name = db.StringProperty(required=True)


class Pager(db.Model):
  """Models a pager (which might be carried by a doctor).

  Attributes:
    number: the phone's number
    name: the phone's name
    doctor: optional reference to Doctor carrying this pager (if any)
  """
  number = db.PhoneNumberProperty(required=True)
  name = db.StringProperty()
  doctor = db.ReferenceProperty(Doctor)


restutil.decorateModuleNamed(__name__)
logging.info('Models in %r decorated', __name__)
