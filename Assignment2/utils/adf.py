import xmltodict
from jsonschema import validate, draft7_format_checker
import logging
from uszipcode import SearchEngine
import re
import fastapi

logger = logging.getLogger(__name__)

# ISO8601 datetime regex
regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
match_iso8601 = re.compile(regex).match
zipcode_search = SearchEngine()

def isNull(obj):
    return obj != obj


def process_before_validating(input_json):
    if isNull(input_json['adf']):
        raise KeyError(f'adf key not found in {input_json}')
    if isNull(input_json['adf']['prospect']):
        raise KeyError(f'prospect key not found in {input_json["adf"]}')

    obj = input_json['adf']['prospect']
    if isNull(obj['id']): raise KeyError(f'id field not found in input_json["adf"]["prospect"]')
    if isNull(obj['customer']): raise KeyError(f'customer field not found in input_json["adf"]["prospect"]')
    if isNull(obj['customer']['contact']): raise KeyError(f'contact field not found in input_json["adf"]["prospect"]["customer"]')
    if isNull(obj['vehicle']): raise KeyError(f'vehicle field not found in input_json["adf"]["prospect"]')

    if isinstance(input_json['adf']['prospect']['id'], dict):
        input_json['adf']['prospect']['id'] = [input_json['adf']['prospect']['id']]
    if isinstance(input_json['adf']['prospect']['customer']['contact'].get('email', {}), str):
        input_json['adf']['prospect']['customer']['contact']['email'] = {
            '@preferredcontact': '0',
            '#text': input_json['adf']['prospect']['customer']['contact']['email']
        }
    if isinstance(input_json['adf']['prospect']['vehicle'].get('price', []), dict):
        input_json['adf']['prospect']['vehicle']['price'] = [input_json['adf']['prospect']['vehicle']['price']]


def validate_iso8601(requestdate):
    try:
        if match_iso8601(requestdate) is not None:
            return True
    except:
        pass
    return False


def is_nan(x):
    return x != x


def parse_xml(adf_xml):
    # use exception handling
    try:
        obj = xmltodict.parse(adf_xml)
        return obj
    except Exception as e:
        logger.error(f'{adf_xml} is not convertable to dict, {e.message}')


def validate_adf_values(input_json):
    try:
        input_json = input_json['adf']['prospect']
        zipcode = input_json['customer']['contact']['address']['postalcode']
        email = input_json['customer']['contact'].get('email', None)
        phone = input_json['customer']['contact'].get('phone', None)
        names = input_json['customer']['contact']['name']
        make = input_json['vehicle']['make']
    except Exception as e:
        logger.error(f'key error in validate_adf_values, {e.message}')
        return {}

    first_name, last_name = False, False
    for name_part in names:
        if name_part.get('@part', '') == 'first' and name_part.get('#text', '') != '':
            first_name = True
        if name_part.get('@part', '') == 'last' and name_part.get('#text', '') != '':
            last_name = True

    logger.info(f'first_name={first_name}, last_name={last_name}, email={email}, phone={phone}')
    if not first_name or not last_name:
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "name is incomplete"}

    if not email and not phone:
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "either phone or email is required"}

    try:
        # zipcode validation
        res = zipcode_search.by_zipcode(zipcode)
        if not res:
            return {"status": "REJECTED", "code": "4_INVALID_ZIP", "message": "Invalid Postal Code"}
    except Exception as e:
        logger.error(f'zipcode_search failed on zipcode={zipcode}')
        return {}

    # check for TCPA Consent
    tcpa_consent = False
    for id in input_json['id']:
        if id['@source'] == 'TCPA_Consent' and id['#text'].lower() == 'yes':
            tcpa_consent = True
    if not email and not tcpa_consent:
        return {"status": "REJECTED", "code": "7_NO_CONSENT", "message": "Contact Method missing TCPA consent"}

    # request date in ISO8601 format
    if not validate_iso8601(input_json['requestdate']):
        return {"status": "REJECTED", "code": "3_INVALID_FIELD", "message": "Invalid DateTime"}

    return {"status": "OK"}


def check_validation(input_json):
    try:
        process_before_validating(input_json)
        validate(
            instance=input_json,
            schema=schema,
            format_checker=draft7_format_checker,
        )
        response = validate_adf_values(input_json)
        if response['status'] == "REJECTED":
            return False, response['code'], response['message']
        return True, "input validated", "validation_ok"
    except Exception as e:
        logger.error(f"Validation failed: {e.message}")
        return False, "6_MISSING_FIELD", e.message
