import json
from collections.abc import Generator
from datetime import date, datetime
from typing import Any
from typing import cast

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from danswer.dynamic_configs.interface import JSON_ro
from danswer.llm.answering.prompts.build import AnswerPromptBuilder, default_build_system_message, \
    default_build_user_message
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

SQL_GENERATION_PROMPT = """your are SQL knowledge expert, your responsible to generate valid SQL script based on user input. 
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
    db_response: str | None = None


class SqlGenerationTool(Tool):
    _NAME = "run_sql_generation"
    _DESCRIPTION = sql_tool_description
    _DISPLAY_NAME = "Sql Generation Tool"

    def __init__(
            self,
            db_session: Session,
            user: User | None,
            persona: Persona,
            prompt_config: PromptConfig,
            llm_config: LLMConfig,
            llm: LLM | None

    ) -> None:
        self.db_session = db_session
        self.user = user
        self.persona = persona
        self.prompt_config = prompt_config
        self.llm_config = llm_config
        self.llm = llm

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
        return args

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
                        sql_generation.db_response
                    }
                    for sql_generation in sql_text_generations
                ]
            }
        )

    def run(self, **kwargs: str) -> Generator[ToolResponse, None, None]:
        query = cast(str, kwargs["query"])

        llm_config = self.llm_config
        history = []
        prompt_builder = AnswerPromptBuilder(history, llm_config)
        prompt_builder.update_system_prompt(
            default_build_system_message(self.prompt_config)
        )
        prompt_builder.update_user_prompt(
            default_build_user_message(
                user_query=query, prompt_config=self.prompt_config, files=[]
            )
        )
        prompt = prompt_builder.build()

        sql_generation_tool_output = message_to_string(
            self.llm.invoke(prompt=prompt)
        )
        # run the SQL in DB
        db_results = self.db_session.execute(text(sql_generation_tool_output))
        # dbrows = db_results.fetchall()
        dbrows = db_results.fetchmany(size=10)

        # Convert rows to a list of dictionaries
        # Each row will be converted to a dictionary using column names
        result_list = [dict(row._mapping) for row in dbrows]

        final_response = ""
        isTableResponse = "json" in query
        if not result_list:
            final_response = "No result found. Please rephrase your query!"
        else:
            if isTableResponse:
                # Define the custom JSON encoder using a lambda function
                json_encoder = lambda obj: obj.isoformat() if isinstance(obj, (date, datetime)) else TypeError(
                    f"Object of type {type(obj).__name__} is not JSON serializable")
                # Serialize the list of dictionaries to a JSON string
                json_result = json.dumps(result_list, default=json_encoder, ensure_ascii=False, indent=4)
                json_response = f"\n\n```json\n{json_result}\n```\n\n"
                final_response = json_response
            else:
                table_response = self.format_as_markdown_table(result_list)
                final_response = table_response

        yield ToolResponse(
            id=SQL_GENERATION_RESPONSE_ID,
            response=final_response
        )


    # Function to format the list of dictionaries as a markdown table
    def format_as_markdown_table(self, data):
        if not data:
            return ""

        # Extract headers from the first dictionary
        headers = data[0].keys()
        # Create the header row
        header_row = "| " + " | ".join(headers) + " |"
        # Create the separator row
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

        # Create the data rows
        data_rows = []
        for row in data:
            row_values = [row[col].isoformat() if isinstance(row[col], (date, datetime)) else str(row[col]) for col in
                          headers]
            data_row = "| " + " | ".join(row_values) + " |"
            data_rows.append(data_row)

        # Combine header, separator, and data rows into a single string
        table = "\n".join([header_row, separator_row] + data_rows)

        return table


    def final_result(self, *args: ToolResponse) -> JSON_ro:
        sql_generation_response = cast(
            list[ToolResponse], args[0].response
        )
        # NOTE: need to do this json.loads(doc.json()) stuff because there are some
        # subfields that are not serializable by default (datetime)
        # this forces pydantic to make them JSON serializable for us
        return sql_generation_response
