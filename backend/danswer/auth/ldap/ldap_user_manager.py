import pandas as pd

from danswer.utils.logger import setup_logger
from danswer.auth.users import get_user_manager
import contextlib
from danswer.auth.schemas import UserCreate
from danswer.auth.schemas import UserRole
from danswer.auth.users import get_user_manager
from danswer.configs.app_configs import SESSION_EXPIRE_TIME_SECONDS
from danswer.db.auth import get_user_count
from danswer.db.auth import get_user_db
from danswer.db.engine import get_async_session
from danswer.db.engine import get_session
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy.orm import Session
from fastapi_users import exceptions
from typing import Any

logger = setup_logger()


async def create_users_from_dataframe(df: pd.DataFrame) -> list[Any]:
    """
    Creates users from a DataFrame and inserts them into the users table.
    :param df: The DataFrame containing user data with columns: email, password, role.
    :return: A list of created user objects.
    """
    created_users = []
    get_async_session_context = contextlib.asynccontextmanager(
        get_async_session
    )  # type:ignore
    get_user_db_context = contextlib.asynccontextmanager(get_user_db)
    get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)

    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                for index, row in df.iterrows():
                    email = row['email']
                    loginid = row['loginid']
                    try:
                        await user_manager.get_by_email(email)
                        logger.info(f"User already exist user: {loginid}")
                        continue
                    except exceptions.UserNotExists:
                        logger.info(f"Creating user: {loginid} from uploaded excel login")

                    # Create the user using the user_manager
                    user: Any = await user_manager.create(
                        UserCreate(
                            email=EmailStr(email),
                            password=loginid,
                            is_verified=True,
                            role=UserRole.BASIC,
                        )
                    )
                    created_users.append(user)

    return created_users
