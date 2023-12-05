import json
from fastapi import APIRouter, Depends
import logging
import time
import fastapi

from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role

router = APIRouter()
logger = logging.getLogger(__name__)

"""
write proper logging and exception handling
"""

def get_quicksight_data(lead_uuid, item):
    """
            Creates the lead converted data for dumping into S3.
            Args:
                lead_uuid: Lead UUID
                item: Accepted lead info pulled from DDB
            Returns:
                S3 data
    """
    data = {
        "lead_hash": lead_uuid,
        "epoch_timestamp": int(time.time()),
        "make": item['make'],
        "model": item['model'],
        "conversion": 1,
        "postalcode": item.get('postalcode', 'unknown'),
        "dealer": item.get('dealer', 'unknown'),
        "3pl": item.get('3pl', 'unknown'),
        "oem_responded": 1
    }
    logger.info(f'get_quicksight_data: created data={data} with lead_uuid={lead_uuid}, item={item}')
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        raise fastapi.HTTPException(status_code=400, detail='lead_uuid or converted fields not found in file body')
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    try:
        oem, role = get_user_role(token)
    except Exception as e:
        logger.error(f'Exception occured at get_user_role with token={token}: {e.message}')
        return {}

    if role != "OEM":
        # throw proper HTTPException
        raise fastapi.HTTPException(status_code=404, detail='User role is not OEM')

    try:
        is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    except Exception as e:
        logger.error(f'Exception occured at db_helper_session.update_lead_conversion with params={(lead_uuid, oem, converted)}: {e.message}')
        return {}

    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logger.info(f's3_helper_client.put_file successful with data={data}, path={path}')
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        raise fastapi.HTTPException(status_code=403, detail='Unable to update lead conversion')
