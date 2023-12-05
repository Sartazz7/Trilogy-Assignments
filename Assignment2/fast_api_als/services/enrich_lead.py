import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session
from types import SimpleNamespace

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    adf_obj = json.loads(adf_json, object_hook=lambda d: SimpleNamespace(**d))
    
    if not adf_obj:
        raise TypeError(f'{adf_json} cannot be converted to object')
    for key in adf_json.keys():
        if not adf_obj[key]:
            raise KeyError(f'{adf_obj} doesn\'t contains key={key}')
    
    return adf_obj