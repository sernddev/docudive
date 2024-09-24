import os
import enum
import json

from typing import Dict, List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

import hashlib
from fastapi import Header, Response
from typing import Optional

from sqlalchemy.orm import Session
from danswer.db.engine import get_session

from danswer.auth.users import current_admin_user
from danswer.auth.users import current_user
from danswer.db.models import User
from danswer.db.persona import get_personas
from danswer.server.settings.models import Settings, KeyValueStoreGeneric, PluginInfoStore

from danswer.server.settings.store import load_settings, store_settings, store_key_value, load_key_value, \
    delete_key_value_generic, get_image_from_key_store, load_plugin_info, store_plugin_info

from danswer.configs.app_configs import IMAGE_SERVER_PROTOCOL
from danswer.configs.app_configs import IMAGE_SERVER_HOST
from danswer.configs.app_configs import IMAGE_SERVER_PORT
from danswer.utils.logger import setup_logger

USER_INFO_KEY = "USER_INFO_"
PLUGIN_INFO_KEY = "PLUGIN_INFO_"
PLUGIN_TAG = "PLUGIN_TAG"
IMAGE_URL = "IMAGE_URL"
AVAILABLE_TAGS = "AVAILABLE_TAGS"

admin_router = APIRouter(prefix="/admin/settings")
basic_router = APIRouter(prefix="/settings")
logger = setup_logger()


@admin_router.put("")
def put_settings(
        settings: Settings, _: User | None = Depends(current_admin_user)
) -> None:
    try:
        settings.check_validity()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store_settings(settings)


@basic_router.get("")
def fetch_settings(_: User | None = Depends(current_user)) -> Settings:
    return load_settings()


@basic_router.put("/user_info")
def upsert_user_info(user_info: KeyValueStoreGeneric, _: User | None = Depends(current_user)) -> None:
    key = f"{USER_INFO_KEY}{user_info.key}"
    logger.info(f"Before inserting Key_Value_Store with key : {key}")
    kvstore = KeyValueStoreGeneric(key=key, value=user_info.value)
    store_key_value(kvstore)
    logger.info(f"Key_Value_Store is updated with key : {key} and the value is {user_info.value}")


@basic_router.get('/user_info/{key}')
def get_user_info(key: str, _: User | None = Depends(current_user)) -> KeyValueStoreGeneric:
    key = f"{USER_INFO_KEY}{key}"
    logger.info(f"Getting USER_INFO from Key_Value_Store with key : {key}")
    kvstore = load_key_value(key)
    if kvstore is None:
        kvstore = KeyValueStoreGeneric(key=key, value="'Your Name' not provided")
    return kvstore


@basic_router.delete('/user_info/{key}')
def delete_user_info(key: str, _: User | None = Depends(current_user)) -> None:
    key = f"{USER_INFO_KEY}{key}"
    delete_key_value_generic(key)
    logger.info(f"key : {key} is deleted from Key_Value_Store")


@basic_router.put("/plugin_info/{plugin_id}")
def upsert_plugin_info(plugin_id: str,  info: PluginInfoStore, _: User | None = Depends(current_user)) -> None:
    key = f"{PLUGIN_INFO_KEY}{plugin_id}"
    store_plugin_info(key, info)


@basic_router.get('/plugin_info/{plugin_id}')
def get_plugin_info(plugin_id: str, _: User | None = Depends(current_user)) -> PluginInfoStore | None:
    key = f"{PLUGIN_INFO_KEY}{plugin_id}"
    return load_plugin_info(key)


@basic_router.delete('/plugin_info/{plugin_id}')
def delete_plugin_info(plugin_id: str, _: User | None = Depends(current_user)) -> None:
    key = f"{PLUGIN_INFO_KEY}{plugin_id}"
    delete_key_value_generic(key)


@basic_router.put("/image_url")
def upsert_image_url(user_info: KeyValueStoreGeneric, _: User | None = Depends(current_user)) -> None:
    key = f"{PLUGIN_INFO_KEY }{user_info.key}"
    logger.info(f"Inserting plugin_info with image_url for key : {key}")
    plugin_info = load_plugin_info(key)
    plugin_info.image_url = user_info.value
    upsert_plugin_info(user_info.key, plugin_info)
    # Invalidate the cache
    #get_image_from_key_store.cache_clear()
    # Optionally reload the updated key into the cache
    get_image_from_key_store(key)


def generate_etag(content: dict[str, str]) -> str:
    # Generate ETag by hashing the serialized content (image_dict)
    content_str = str(sorted(content.items()))  # Sort to ensure consistent ordering
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()


@basic_router.get('/image_url')
def get_all_images(response: Response, if_none_match: Optional[str] = Header(None),
                   _: User | None = Depends(current_user),
                   db_session: Session = Depends(get_session),
                   include_deleted: bool = False) -> dict[str, str] | None:
    image_dict: dict[str, str] = {}
    persona_ids = [
        persona.id
        for persona in get_personas(
            db_session=db_session,
            user_id=None,  # user_id = None -> give back all personas
            include_deleted=include_deleted,
        )
    ]

    for persona_id in persona_ids:
        key = f"{PLUGIN_INFO_KEY}{persona_id}"
        image_url = get_image_from_key_store(key)
        image_dict[str(persona_id)] = "" if image_url is None else image_url

    # Generated ETag based on the image_dict content
    etag = generate_etag(image_dict)

    if if_none_match == etag:
        # if ETag matches, returns 304 Not Modified
        response.status_code = 304
        return

    response.headers['ETag'] = etag

    return image_dict


@basic_router.get('/image_url/{key}')
def get_image_url(key: str, _: User | None = Depends(current_user)) -> str | None:
    key = f"{PLUGIN_INFO_KEY}{key}"
    return get_image_from_key_store(key)


@basic_router.delete('/image_url/{key}')
def delete_image_url(key: str,  _: User | None = Depends(current_user)) -> None:
    key = f"{PLUGIN_INFO_KEY}{key}"
    plugin_info = load_plugin_info(key)
    plugin_info.image_url = ""
    upsert_plugin_info(key, plugin_info)
    #get_image_from_key_store.cache_clear()


@basic_router.get("/icons")
def get_image_urls(_: User | None = Depends(current_user)) -> dict[str, list[str]]:
    directory_path = "/icons"  # Change this to your directory path
    image_urls = list_image_urls(directory_path)
    return {"icons_urls": image_urls}


def list_image_urls(directory_path: str):
    """
    Lists all imaes URLs from the given directory.
    """
    IMAGE_SERVER_BASE_URL = get_image_server_url()
    image_urls = []
    try:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    image_url = IMAGE_SERVER_BASE_URL + relative_path.replace("\\", "/")
                    image_urls.append(image_url)
    except Exception as ex:
        logger.error(
            f"error while fetching icons from dir path: {directory_path} : ref img url:  {IMAGE_SERVER_BASE_URL}. Error: {ex}")
    return image_urls


def get_image_server_url():
    return IMAGE_SERVER_PROTOCOL + "://" + IMAGE_SERVER_HOST + ":" + IMAGE_SERVER_PORT + "/" + "icons/"
