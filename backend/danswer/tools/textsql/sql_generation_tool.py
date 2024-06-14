import json
from collections.abc import Generator
from typing import Any
from typing import cast

from pydantic import BaseModel

from danswer.chat.chat_utils import combine_message_chain
from danswer.configs.model_configs import GEN_AI_HISTORY_CUTOFF
from danswer.llm.utils import message_to_string
from danswer.prompts.constants import GENERAL_SEP_PAT
from danswer.tools.tool import Tool
from danswer.tools.tool import ToolResponse
from danswer.utils.logger import setup_logger
from danswer.db.models import Persona
from danswer.db.models import User
from danswer.llm.answering.models import PromptConfig, PreviousMessage
from danswer.llm.interfaces import LLMConfig, LLM

logger = setup_logger()

SQL_GENERATION_RESPONSE_ID = "sql_generation_response"

sql_tool_description = """
Runs query on LLM to get SQL. 
HINT: if input question as about sql generation use this tool.
"""
YES_SQL_GENERATION = "YES"
SKIP_SQL_GENERATION = "NO"

SQL_GENERATION_TEMPLATE = f"""
Given the conversation history and a follow up query, determine if the system should call \
an external SQL generation tool to better answer the latest user input. If user query is related to database, or it query related response should be {YES_SQL_GENERATION}.
Your default response is {SKIP_SQL_GENERATION}.

Respond "{YES_SQL_GENERATION}" if:
- The user is asking for an SQL to be generated.

Conversation History:
{GENERAL_SEP_PAT}
{{chat_history}}
{GENERAL_SEP_PAT}

If you are at all unsure, respond with {SKIP_SQL_GENERATION}.
Respond with EXACTLY and ONLY "{SKIP_SQL_GENERATION}" or "{YES_SQL_GENERATION}"

Follow Up Input:
{{final_query}}
""".strip()

SQL_GENERATION_PROMPT="""your are SQL knowledge expert, your responsible to generate valid SQL script based on user input. 
do not add any explanation, do not makeup any answer. don't use your knowledge. based on provided meta data generate SQL query.

always generate SQL query using only following tables, don't use tables which is not in below list. Don't generate any additional details or explanation except SQL.

tables and columns to use:
Album(AlbumId  primary key, Title, ArtistId)
Artist(ArtistId primary key,Name)
Customer(CustomerId primary key,FirstName,LastName,Company,Address,City,State,Country)
Employee(EmployeeId primary key,FirstName,LastName,Title,ReportsTo, BirthDate,Address,City,State,Country,Phone,Email)



QUERY: <USER_QUERY>
RESPONSE:"""



class SqlGenerationResponse(BaseModel):
    sql: str | None = None


class SqlGenerationTool(Tool):
    def __init__(
            self,
            user: User | None,
            persona: Persona,
            prompt_config: PromptConfig,
            llm_config: LLMConfig,

    ) -> None:
        self.user = user
        self.persona = persona
        self.prompt_config = prompt_config
        self.llm_config = llm_config

    @classmethod
    def name(cls) -> str:
        return "run_sql_generation"

    """For explicit tool calling"""
    @classmethod
    def tool_definition(cls) -> dict:
        return {
            "type": "function",
            "function": {
                "name": cls.name(),
                "description": sql_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt used to generate the SQL statement",
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
        if force_run:
            return args

        history_str = combine_message_chain(
            messages=history, token_limit=GEN_AI_HISTORY_CUTOFF
        )
        prompt = SQL_GENERATION_TEMPLATE.format(
            chat_history = None,
            final_query=query,
        )

        use_sql_generation_tool_output = message_to_string(llm.invoke(prompt))
        #logger.log("SqlGenerationTool: get_args_for_non_tool_calling_llm")
        #logger.debug(            f"Evaluated if should use SqlGenerationTool: {use_sql_generation_tool_output}")
        if (
                YES_SQL_GENERATION.split()[0]
        ).lower() in use_sql_generation_tool_output.lower():
            # return args

             return {"sql" : "select count(1) frm employees"}

        return None

    def build_tool_message_content(
            self, *args: ToolResponse
    ) -> str | list[str | dict[str, Any]]:
        generation_response = args[0]
        sql_text_generations = cast(
            list[SqlGenerationResponse], generation_response.response
        )
        return json.dumps(
            {
                "search_results": [
                    {
                        sql_generation.sql
                    }
                    for sql_generation in sql_text_generations
                ]
            }
        )

    def run(self, **kwargs: str) -> Generator[ToolResponse, None, None]:
        query = cast(str, kwargs["sql"])

        # yield ToolResponse(
        #     id=SQL_GENERATION_RESPONSE_ID,
        #     response=SqlGenerationResponse(
        #         sql=query
        #     ),
        # )
        yield ToolResponse(
            id=SQL_GENERATION_RESPONSE_ID,
            response=query
        )
