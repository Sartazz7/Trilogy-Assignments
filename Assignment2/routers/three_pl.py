import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        logger.info(f'body from request in /reset_authkey: {body}')
        provider, role = get_user_role(token)
        logger.info(f'provider={provider}, role={role} from get_user_role in /reset_authkey')

        if role != "ADMIN" and (role != "3PL"):
            pass
        if role == "ADMIN":
            provider = body['3pl']
        apikey = db_helper_session.set_auth_key(username=provider)
        return {
            "status_code": HTTP_200_OK,
            "x-api-key": apikey
        }
    except Exception as e:
        logger.error(f'post request on /reset_authkey failed with error: {e}')
        return {}


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        logger.info(f'body from request in /view_authkey: {body}')
        provider, role = get_user_role(token)
        logger.info(f'provider={provider}, role={role} from get_user_role in /view_authkey')

        if role != "ADMIN" and role != "3PL":
            pass
        if role == "ADMIN":
            provider = body['3pl']
        apikey = db_helper_session.get_auth_key(username=provider)
        return {
            "status_code": HTTP_200_OK,
            "x-api-key": apikey
        }
    except Exception as e:
        logger.error(f'post request on /view_authkey failed with error: {e}')
        return {}
