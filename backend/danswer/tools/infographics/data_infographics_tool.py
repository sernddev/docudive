import json
from collections.abc import Generator
from typing import Any
from typing import cast

from pydantic import BaseModel
from sqlalchemy.orm import Session

from danswer.db.models import Persona
from danswer.db.models import User
from danswer.dynamic_configs.interface import JSON_ro
from danswer.file_store.models import InMemoryChatFile
from danswer.llm.answering.models import PromptConfig, PreviousMessage
from danswer.llm.interfaces import LLMConfig, LLM
from danswer.tools.infographics.exceptions import DataframeInMemorySQLExecutionException, LLMException
from danswer.tools.infographics.plot_summarize_generate_sql import PlotSummarizeGenerateSQL
from danswer.tools.tool import Tool
from danswer.tools.tool import ToolResponse
from danswer.tools.utils import get_current_or_previous_files
from danswer.utils.logger import setup_logger

logger = setup_logger()

FILE_DATA_INFOGRAPHICS_RESPONSE_ID = "file_data_infographics_response_id"

FILE_DATA_INFOGRAPHICS_TOOL_DESCRIPTION = """
Runs query on LLM to suggest insightful graph and summary from the attached file.
"""

SUMMARIZATION_PROMPT_FOR_TABULAR_DATA = """Your Knowledge expert acting as data analyst, your responsible for generating short summary in 100 words based on give tabular data.
Give tabular data is out of this query {}
Tabular data is {}

analyze above tabular data and user query, try to identify domain data and provide title and summary in paragraphs and bullet points, DONT USE YOUR EXISTING KNOWLEDGE.

"""


class FileDataInfoGraphicsResponse(BaseModel):
    db_response: str | None = None


class FileDataInfographicsTool(Tool):
    _NAME = "File Data Infographics"
    _DESCRIPTION = FILE_DATA_INFOGRAPHICS_TOOL_DESCRIPTION
    _DISPLAY_NAME = "File Data Infographics Tool"

    def __init__(
            self,
            history: list[PreviousMessage],
            db_session: Session,
            user: User | None,
            persona: Persona,
            prompt_config: PromptConfig,
            llm_config: LLMConfig,
            llm: LLM | None,
            files: list[InMemoryChatFile] | None,
            metadata: dict | None

    ) -> None:
        self.history = history
        self.db_session = db_session
        self.user = user
        self.persona = persona
        self.prompt_config = prompt_config
        self.llm_config = llm_config
        self.llm = llm
        self.files = files
        self.metadata = metadata,
        self.plot_summarize_sql = PlotSummarizeGenerateSQL(self.llm, self.llm_config, self.prompt_config)

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
                            "description": "Prompt used to generate infographics for the file data",
                        },
                    },
                    "required": ["prompt"],
                },
            },
        }

    def get_args_for_non_tool_calling_llm(self,
                                          query: str,
                                          history: list[PreviousMessage],
                                          llm: LLM,
                                          force_run: bool = False) -> dict[str, Any] | None:
        # rephrased_query = history_based_query_rephrase(query=query, history=history, llm=llm)
        return {"query": query}

    def build_tool_message_content(
            self, *args: ToolResponse
    ) -> str | list[str | dict[str, Any]]:
        generation_response = args[0]
        tool_text_generations = cast(
            list[FileDataInfoGraphicsResponse], generation_response.response
        )
        return json.dumps(
            {
                "search_results": [
                    {
                        tool_generation.db_response
                    }
                    for tool_generation in tool_text_generations
                ]
            }
        )

    def run(self, **kwargs: str) -> Generator[ToolResponse, None, None]:
        query = cast(str, kwargs["query"])
        try:
            files = get_current_or_previous_files(self.files, self.history)
            file = files[0] if files else None
            if file:
                _, filtered_df, sql_generation_tool_output = self.plot_summarize_sql.generate_execute_sql_dataframe(file,
                                                                                                                    query,
                                                                                                                    metadata=self.metadata)
                image_path = self.plot_summarize_sql.resolve_parameters_and_generate_chart(sql_query=sql_generation_tool_output,
                                                                                           filtered_df=filtered_df,
                                                                                           user_requirement=query,
                                                                                           metadata=self.metadata)
                logger.info(f'sql_generation_tool:: image_path: {image_path}, filtered_df: {filtered_df}')
                if filtered_df is not None and not filtered_df.empty:
                    list_records = filtered_df.to_dict('records')
                    tabular_data_summarization = self.tabular_data_summarizer(query, list_records)
                else:
                    logger.info(f'filtered_df returned from plot_summarize_or_regenerate_sql is empty: {filtered_df}')
                    tabular_data_summarization = 'No data to summarize.'
                tool_output = tabular_data_summarization + "\n" + image_path
            else:
                tool_output = 'No file found to perform infographics analysis. Please upload a file.'
        except Exception as e:
            logger.exception(f'Exception: {str(e)}')
            if isinstance(e, DataframeInMemorySQLExecutionException):
                tool_output = "Exception received while Executing SQL. No data found."
            if isinstance(e, LLMException):
                tool_output = "Exception received while querying LLM."
            else:
                tool_output = 'Exception while serving the request. Try reforming the query and or uploading another file.'

        yield ToolResponse(
            id=FILE_DATA_INFOGRAPHICS_RESPONSE_ID,
            response=tool_output
        )


    def tabular_data_summarizer(self, user_query, tabular_data: list):

        #formatted_table = "\n".join(["\t".join(row) for row in tabular_data])
        #SUMMARIZATION_PROMPT_FOR_TABULAR_DATA.format(user_query, formatted_table)
        logger.info(SUMMARIZATION_PROMPT_FOR_TABULAR_DATA)

        llm_response = self.llm.invoke(prompt=SUMMARIZATION_PROMPT_FOR_TABULAR_DATA.format(user_query, tabular_data), metadata=self.metadata)
        sql_query = llm_response.content

        return sql_query

    def final_result(self, *args: ToolResponse) -> JSON_ro:
        tool_generation_response = cast(
            list[ToolResponse], args[0].response
        )
        # NOTE: need to do this json.loads(doc.json()) stuff because there are some
        # subfields that are not serializable by default (datetime)
        # this forces pydantic to make them JSON serializable for us
        return tool_generation_response
