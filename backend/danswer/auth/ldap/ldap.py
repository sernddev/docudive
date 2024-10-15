import os
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.password import PasswordHelper
from sqlalchemy.orm import Session
from danswer.db.engine import get_session
from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, Strategy
from fastapi_users.manager import BaseUserManager
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.router.common import ErrorCode, ErrorModel

from danswer.auth.ldap.ldap_with_details import LDAPAuthenticator, LDAPResponseModel
from danswer.auth.schemas import  UserRole
from danswer.db.models import User
from danswer.configs.app_configs import LDAP_SERVER, LDAP_DOMAIN, GROUP_DNS
from fastapi_users import exceptions

from danswer.server.settings.models import UserInfoStore
from danswer.server.settings.store import store_user_info

os.environ['SUPER_USER']="NO_USER"

def get_ldap_auth_router(
        self,
        backend: AuthenticationBackend ,
        requires_verification: bool = False
) -> APIRouter:
    router = APIRouter()
    get_current_user_token = self.authenticator.current_user_token(
        active=True, verified=requires_verification
    )

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value": {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
            request: Request,
            credentials: OAuth2PasswordRequestForm = Depends(),
            user_manager: BaseUserManager[models.UP, models.ID] = Depends(self.get_user_manager),
            strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
            db_session: Session = Depends(get_session),
    ):
        ldap_authenticator: LDAPAuthenticator = LDAPAuthenticator(LDAP_SERVER, LDAP_DOMAIN)
        ## 1. check LDAP authentication
        response = ldap_authenticator.authenticate(credentials.username,credentials.password)
        if not response.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        ## 1. Create current user as SUPER ADMIN  if no Active ADMIN exists in system
        #create the first admin user
        SUPER_USER = os.getenv('SUPER_USER', "NO_USER")
        if SUPER_USER =="NO_USER":
            active_super_User = await get_active_superuser(db_session=db_session)
            if active_super_User is None:
                await create_first_superuser(db_session=db_session,
                                             user_password=credentials.password,
                                             ldap_response= response)



        try:
            user = await user_manager.get_by_email(response.email)
        except exceptions.UserNotExists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not set up in the system.",
            )

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not activated.",
            )
        response = await backend.login(strategy, user)
        await user_manager.on_after_login(user, request, response)
        return response

    logout_responses: OpenAPIResponseType = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user."
            }
        },
        **backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post(
        "/logout", name=f"auth:{backend.name}.logout", responses=logout_responses
    )
    async def logout(
            user_token: Tuple[models.UP, str] = Depends(get_current_user_token),
            strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user, token = user_token
        return await backend.logout(strategy, user, token)

    return router

async def create_first_superuser(db_session:Session,
                                 user_password:str,
                                 ldap_response: LDAPResponseModel) -> bool:
    try:
        passwordHelper = PasswordHelper()
        new_user = User(email=ldap_response.email,
                        hashed_password=passwordHelper.hash(user_password),
                        is_active=True,
                        role=UserRole.ADMIN
                        )
        db_session.add(new_user)
        db_session.commit()
        os.environ['SUPER_USER'] = ldap_response.login_id
    except exceptions.UserAlreadyExists or exceptions.Any:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive Super Users in the system.",
        )
    user_key=f"USER_INFO_{ldap_response.email}"
    userinfo = UserInfoStore(email= ldap_response.email,
                             loginid= ldap_response.login_id,
                             first_name=ldap_response.first_name,
                             full_name= ldap_response.full_name)

    store_user_info(key=user_key,user_info= userinfo)

    return True

async def get_active_superuser(db_session: Session) -> User | None:
    user = db_session.query(User).filter(User.role == UserRole.ADMIN,User.is_active==True).first()  # type: ignore
    return user