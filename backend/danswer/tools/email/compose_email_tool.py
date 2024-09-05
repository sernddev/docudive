import json
from collections.abc import Generator
from typing import Any
from typing import cast
from pydantic import BaseModel

from danswer.dynamic_configs.interface import JSON_ro
from danswer.llm.answering.prompts.build import AnswerPromptBuilder, default_build_system_message, \
    default_build_user_message
from danswer.llm.utils import message_to_string, message_generator_to_string_generator
from danswer.server.settings.api import get_user_info
from danswer.tools.tool import Tool
from danswer.tools.tool import ToolResponse
from danswer.utils.logger import setup_logger
from danswer.db.models import Persona
from danswer.db.models import User
from danswer.llm.answering.models import PromptConfig, PreviousMessage
from danswer.llm.interfaces import LLMConfig, LLM
from danswer.tools.email.send_email import EmailService

logger = setup_logger()

COMPOSE_EMAIL_RESPONSE_ID = "compose_email_response"

Compose_email_tool_description = """
Runs query on LLM to compose email. 
HINT: if input question as about composing or drafting an email, then use this tool.
"""

Compose_Email_TEMPLATE = f"""
provide email subject always in this format, **Subject**

example:

**Subject**: Sick Leave
Dear Hr,
I am on sick leave for 2 days starting from today,

Regards,
Name
""".strip()

COMPOSE_EMAIL_PROMPT = """You are a professional email writing assistant that always uses a polite enthusiastic tone, 
emphasizes action items, and leaves blanks for the human to fill in when you have unknowns.

QUERY: <USER_QUERY>
RESPONSE:"""


class ComposeEmailResponse(BaseModel):
    Summary: str | None = None


class ComposeEmailTool(Tool):
    _NAME = "run_compose_email"
    _DESCRIPTION = Compose_email_tool_description
    _DISPLAY_NAME = "Compose Email Tool"

    def __init__(
            self,
            user: User | None,
            persona: Persona,
            prompt_config: PromptConfig,
            llm_config: LLMConfig,
            llm: LLM | None
    ) -> None:
        self.history = None
        self.user = user
        self.persona = persona
        self.prompt_config = prompt_config
        self.llm_config = llm_config
        self.llm = llm

        logger.info(f"Logged in user details: {'not logged in' if self.user is None else self.user.email}")

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def description(self) -> str:
        return self._DESCRIPTION

    @property
    def display_name(self) -> str:
        return self._DISPLAY_NAME

    """For explicit tool calling"""

    def tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt used to Compose the Email",
                        },
                    },
                    "required": ["prompt"],
                },
            },
        }

    def get_args_for_non_tool_calling_llm(
            self,
            query: str,
            history: list[PreviousMessage],
            llm: LLM,
            force_run: bool = False,
    ) -> dict[str, Any] | None:
        args = {"query": query}
        self.history = history
        return args

    def build_tool_message_content(
            self, *args: ToolResponse
    ) -> str | list[str | dict[str, Any]]:
        compose_email_response = args[0]
        compose_email_text = cast(
            list[ComposeEmailResponse], compose_email_response.response
        )
        return json.dumps(
            {
                "search_results": [
                    {
                        Compose_email.Summary
                    }
                    for Compose_email in compose_email_text
                ]
            }
        )

    def run(self, **kwargs: str) -> Generator[ToolResponse, None, None]:

        logger.info(f"Email plugin - mail composing started")

        query = cast(str, kwargs["query"])

        name = get_user_info(self.user.email)

        query = f"{query} and my name is { 'Your Name' if name is None else name.value}"

        prompt_builder = AnswerPromptBuilder(self.history, self.llm_config)

        prompt_builder.update_system_prompt(
            default_build_system_message(self.prompt_config)
        )

        prompt_builder.update_user_prompt(
            default_build_user_message(
                user_query=query, prompt_config=self.prompt_config, files=[]
            )
        )
        prompt = prompt_builder.build()

        mail_response = message_to_string(
            self.llm.invoke(prompt=prompt)
        )

        logger.info(f"Email plugin - mail composing completed")

        yield ToolResponse(
            id=COMPOSE_EMAIL_RESPONSE_ID,
            response=mail_response
        )

    def final_result(self, *args: ToolResponse) -> JSON_ro:
        composed_email_response = cast(
            list[ToolResponse], args[0].response
        )
        # NOTE: need to do this json.loads(doc.json()) stuff because there are some
        # subfields that are not serializable by default (datetime)
        # this forces pydantic to make them JSON serializable for us
        return composed_email_response
