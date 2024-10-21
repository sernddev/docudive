import logging
from typing import cast

from danswer.dynamic_configs.factory import get_dynamic_config_store
from danswer.dynamic_configs.interface import ConfigNotFoundError
from danswer.server.settings.models import Settings, KeyValueStoreGeneric, PluginInfoStore, UserInfoStore
from danswer.utils.logger import setup_logger
from functools import lru_cache

_SETTINGS_KEY = "danswer_settings"
logger = setup_logger()


def load_settings() -> Settings:
    dynamic_config_store = get_dynamic_config_store()
    try:
        settings = Settings(**cast(dict, dynamic_config_store.load(_SETTINGS_KEY)))
    except ConfigNotFoundError:
        settings = Settings()
        dynamic_config_store.store(_SETTINGS_KEY, settings.dict())
    return settings


def store_settings(settings: Settings) -> None:
    get_dynamic_config_store().store(_SETTINGS_KEY, settings.dict())


#@lru_cache(maxsize=50)
def get_image_from_key_store(key) -> str | None:
    return None if load_plugin_info(key) is None else load_plugin_info(key).image_url


def store_key_value(kvstore: KeyValueStoreGeneric) -> None:
    get_dynamic_config_store().store(kvstore.key, kvstore.dict())

def store_user_info(key: str, user_info: UserInfoStore) -> None:
    get_dynamic_config_store().store(key, user_info.dict())

def load_user_info(key) -> UserInfoStore | None:
    dynamic_config_store = get_dynamic_config_store()
    try:
        data = dynamic_config_store.load(key)
        if data is None:
            logger.warning(f"No data found for key: {key}")
            info = None
        else:
            info = UserInfoStore(**cast(dict, data))
    except ConfigNotFoundError as ex:
        logger.error(f"Error occurred during load_user_info for key: {key} Exception: {ex}")
        info = None
    return info

def delete_key_value_generic(key) -> None:
    get_dynamic_config_store().delete(key)

def store_plugin_info(key: str, plugin_info: PluginInfoStore) -> None:
    get_dynamic_config_store().store(key, plugin_info.dict())

def load_plugin_info(key) -> PluginInfoStore | None:
    dynamic_config_store = get_dynamic_config_store()
    try:
        data = dynamic_config_store.load(key)
        if data is None:
            logger.warning(f"No data found for key: {key}")
            info = None
        else:
            info = PluginInfoStore(**cast(dict, data))
    except ConfigNotFoundError as ex:
        logger.error(f"Error occurred during load_plugin_info for key: {key} Exception: {ex}")
        info = None
    return info



