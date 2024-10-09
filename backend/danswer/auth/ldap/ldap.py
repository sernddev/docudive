import contextlib
import secrets
from typing import Any, Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi_users import exceptions
from fastapi_users.password import PasswordHelper
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy.orm import Session

from danswer.auth.ldap.ldap_with_details import LDAPResponseModel
from danswer.auth.ldap_with_details import LDAPAuthenticator
from danswer.auth.schemas import UserCreate
from danswer.auth.schemas import UserRole
from danswer.auth.users import get_user_manager
from danswer.configs.app_configs import SESSION_EXPIRE_TIME_SECONDS
from danswer.db.auth import get_user_count
from danswer.db.auth import get_user_db
from danswer.db.engine import get_async_session
from danswer.db.engine import get_session
from danswer.db.models import User
from danswer.utils.logger import setup_logger
from ee.danswer.db.saml import upsert_saml_account, get_saml_account, expire_saml_account
from ee.danswer.utils.secrets import encrypt_string, extract_hashed_cookie

logger = setup_logger()
router = APIRouter(prefix="/auth/ldap")



async def upsert_ldap_user(email: str) -> User:
    get_async_session_context = contextlib.asynccontextmanager(
        get_async_session
    )  # type:ignore
    get_user_db_context = contextlib.asynccontextmanager(get_user_db)
    get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)

    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                try:
                    return await user_manager.get_by_email(email)
                except exceptions.UserNotExists:
                    logger.info("Creating user from LDAP login")

                user_count = await get_user_count()
                role = UserRole.ADMIN if user_count == 0 else UserRole.BASIC

                fastapi_users_pw_helper = PasswordHelper()
                password = fastapi_users_pw_helper.generate()
                hashed_pass = fastapi_users_pw_helper.hash(password)

                user: User = await user_manager.create(
                    UserCreate(
                        email=EmailStr(email),
                        password=hashed_pass,
                        is_verified=True,
                        role=role,
                    )
                )

                return user


async def prepare_from_fastapi_request(request: Request) -> dict[str, Any]:
    '''
    we supposed to get login id and password here need to update this code
    :param request:
    :return:
    '''
    form_data = await request.form()
    if request.client is None:
        raise ValueError("Invalid request for LDAP")

    rv: dict[str, Any] = {
        "http_host": request.client.host,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "post_data": {},
        "get_data": {},
    }
    if request.query_params:
        rv["get_data"] = (request.query_params,)
    if "SAMLResponse" in form_data:
        SAMLResponse = form_data["SAMLResponse"]
        rv["post_data"]["SAMLResponse"] = SAMLResponse
    if "RelayState" in form_data:
        RelayState = form_data["RelayState"]
        rv["post_data"]["RelayState"] = RelayState

        # Parse the request body (JSON) if present
    try:
        json_body = await request.json()
        rv["body_data"].update(json_body)
    except Exception:
        # If body is not JSON, skip
        pass
    return rv





@router.post("/authorize")
async def ldap_login(request: Request) -> LDAPResponseModel:
    req: dict[str, Any] = await prepare_from_fastapi_request(request)
    server = "get it from env"
    domain = "get it from env"
    auth = LDAPAuthenticator(server_address=server, domain=domain)
    response = auth.login()

    if not response.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="login failed",
        ) # return error login failed

    user_email = response.email
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LDAP is not set up correctly, email attribute must be provided.",
        )


    user = await upsert_ldap_user(email=user_email)

    # Generate a random session cookie and Sha256 encrypt before saving
    session_cookie = secrets.token_hex(16)
    saved_cookie = encrypt_string(session_cookie)

    #uncomment below code
    #upsert_saml_account(user_id=user.id, cookie=saved_cookie, db_session=db_session)

    # Redirect to main Danswer search page
    response = Response(status_code=status.HTTP_204_NO_CONTENT)

    response.set_cookie(
        key="session",
        value=session_cookie,
        httponly=True,
        secure=True,
        max_age=SESSION_EXPIRE_TIME_SECONDS,
    )


    return response


@router.post("/callback")
async def ldap_login_callback(
    request: Request,
    db_session: Session = Depends(get_session),
) :
    req = await prepare_from_fastapi_request(request)

    responses = "this is not require callback, will be disabled"

    return response


@router.post("/logout")
def ldap_logout(
    request: Request,
    db_session: Session = Depends(get_session),
) -> None:
    saved_cookie = extract_hashed_cookie(request)

    if saved_cookie:
        saml_account = get_saml_account(cookie=saved_cookie, db_session=db_session)
        if saml_account:
            expire_saml_account(saml_account, db_session)

    return
