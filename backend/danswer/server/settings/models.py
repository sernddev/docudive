from enum import Enum
from typing import List
from pydantic import BaseModel


class PageType(str, Enum):
    CHAT = "chat"
    SEARCH = "search"


# This model used to store and retrieve plugin information from DB
class KeyValueStoreGeneric(BaseModel):
    key: str
    value: str


# This model used to store and retrieve plugin information from DB
class PluginInfoStore(BaseModel):
    image_url: str | None = None
    plugin_tags: List[str] | None = None
    supports_file_upload: bool = True
    supports_temperature_dialog: bool = True
    custom_message_water_mark: str = "Send a message"
    is_recommendation_supported: bool = False
    recommendation_prompt: str | None = None
    is_favorite: bool = False
    is_arabic: bool = False


class Settings(BaseModel):
    """General settings"""

    chat_page_enabled: bool = True
    search_page_enabled: bool = True
    default_page: PageType = PageType.SEARCH
    maximum_chat_retention_days: int | None = None

    def check_validity(self) -> None:
        chat_page_enabled = self.chat_page_enabled
        search_page_enabled = self.search_page_enabled
        default_page = self.default_page

        if chat_page_enabled is False and search_page_enabled is False:
            raise ValueError(
                "One of `search_page_enabled` and `chat_page_enabled` must be True."
            )

        if default_page == PageType.CHAT and chat_page_enabled is False:
            raise ValueError(
                "The default page cannot be 'chat' if the chat page is disabled."
            )

        if default_page == PageType.SEARCH and search_page_enabled is False:
            raise ValueError(
                "The default page cannot be 'search' if the search page is disabled."
            )
