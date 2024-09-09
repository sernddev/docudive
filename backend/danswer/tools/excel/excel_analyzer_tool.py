import json
from collections.abc import Generator
from typing import Any
from typing import cast

from pydantic import BaseModel
from sqlalchemy.orm import Session

from danswer.dynamic_configs.interface import JSON_ro
from danswer.file_store.models import InMemoryChatFile
from danswer.llm.answering.prompts.build import AnswerPromptBuilder, default_build_system_message, \
    default_build_user_message, default_build_system_message_by_prmpt, default_build_user_message_by_task_prompt
from danswer.llm.utils import message_to_string
from danswer.secondary_llm_flows.query_expansion import history_based_query_rephrase
from danswer.tools.excel import excel_analyzer_bl
from danswer.tools.tool import Tool
from danswer.tools.tool import ToolResponse
from danswer.tools.utils import generate_dataframe_from_excel
from danswer.utils.logger import setup_logger
from danswer.db.models import Persona, ChatMessage
from danswer.db.models import User
from danswer.llm.answering.models import PromptConfig, PreviousMessage
from danswer.llm.interfaces import LLMConfig, LLM

logger = setup_logger()

EXCEL_ANALYZER_RESPONSE_ID = "excel_analyzer_response"

EXCEL_ANALYZER_TOOL_DESCRIPTION = """
Runs query on LLM to get Excel. 
HINT: if input question as about Excel generation use this tool.
"""

SUMMARIZATION_PROMPT_FOR_TABULAR_DATA = """Your Knowledge expert acting as data analyst, your responsible for generating short summary in 100 words based on give tabular data.
Give tabular data is out of this query {}
Tabular data is {}

analyze above tabular data and user query, try to identify domain data and provide title and summary in paragraphs and bullet points, DONT USE YOUR EXISTING KNOWLEDGE.

"""

'''
Tested with 
System prompt:
### Instruction:
You are a data science assistant. Your task is to take a user's input describing an operation on a pandas DataFrame and convert it into a valid Python DataFrame query that can be executed using eval(). The query should only use valid pandas operations like filtering, grouping, or aggregation.

Ensure that:
1. The query is well-formed and syntactically correct.
2. The query uses safe operations compatible with pandas.
3. The query should operate on a DataFrame named `df`.
4. The output query must be a Python expression that can be evaluated using eval().
5. DONT explain, write only single line python code which can be executed on dataframe using eval()
6. if you didn't understand query or columns not matching write response as "None"

Task Prompt:

### Example 1:
User input: "Group by country and calculate the average salary"
LLM output: "df.groupby('country')['salary'].mean()"

### Example 2:
User input: "Filter rows where age is greater than 30"
LLM output: "df[df['age'] > 30]"

### Example 3:
User input: "Group by country and calculate the mean age and salary"
LLM output: "df.groupby('country').agg({'age': 'mean', 'salary': 'mean'})"

### Example 4:
User input: "Filter rows where sales are above 5000 and country is USA"
LLM output: "df[(df['sales'] > 5000) & (df['country'] == 'USA')]"

Model :llama 70b
'''
SYSTEM_PROMPT = """### Instruction:
You are a data science assistant. Your task is to take a user's input describing an operation on a pandas DataFrame and convert it into a valid Python DataFrame query that can be executed using eval(). The query should only use valid pandas operations like filtering, grouping, or aggregation.

Ensure that:
1. The query is well-formed and syntactically correct.
2. The query uses safe operations compatible with pandas.
3. The query should operate on a DataFrame named `df`.
4. The output query must be a Python expression that can be evaluated using eval().
5. DONT explain, write only single line python code which can be executed on dataframe using eval()
6. if you didn't understand query or columns not matching write response as "None"
"""
TASK_PROMPT = """
### Example 1:
User input: "Group by country and calculate the average salary"
LLM output: "df.groupby('country')['salary'].mean()"

### Example 2:
User input: "Filter rows where age is greater than 30"
LLM output: "df[df['age'] > 30]"

### Example 3:
User input: "Group by country and calculate the mean age and salary"
LLM output: "df.groupby('country').agg({'age': 'mean', 'salary': 'mean'})"

### Example 4:
User input: "Filter rows where sales are above 5000 and country is USA"
LLM output: "df[(df['sales'] > 5000) & (df['country'] == 'USA')]
"""


class ExcelAnalyzerResponse(BaseModel):
    db_response: str | None = None


class ExcelAnalyzerTool(Tool):
    _NAME = "Tabular_Analyzer"
    _DESCRIPTION = EXCEL_ANALYZER_TOOL_DESCRIPTION
    _DISPLAY_NAME = "Tabular Analyzer Tool"

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
        self.metadata = metadata

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
                            "description": "Prompt used to analyze the excel table data",
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
        #rephrased_query = history_based_query_rephrase(query=query, history=history, llm=llm)
        return {"query": query}

    def build_tool_message_content(
            self, *args: ToolResponse
    ) -> str | list[str | dict[str, Any]]:
        generation_response = args[0]
        tool_text_generations = cast(
            list[ExcelAnalyzerResponse], generation_response.response
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
        file = None
        if not self.files:
            # Fetch last file
            previous_msgs = self.history[0]
            if previous_msgs.files:
                file = previous_msgs.files[0]
        else:
            file = self.files[0]

        if file:
            dataframe = generate_dataframe_from_excel(file)
            quer_with_schema = "dataframe schema with fields: \n" + str(
                dataframe.dtypes) + "\n\n" + "sample data: \n" + str(dataframe.head(5)) + f"\nuser query: {query}"
            # send query to LLM to get pandas functions, out put should be valid pandas function
            prompt_builder = AnswerPromptBuilder(self.history, self.llm_config)
            prompt_builder.update_system_prompt(
                default_build_system_message_by_prmpt(SYSTEM_PROMPT)
            )
            prompt_builder.update_user_prompt(
                default_build_user_message_by_task_prompt(
                    user_query=quer_with_schema, task_prompt=TASK_PROMPT, files=[]
                )
            )
            prompt = prompt_builder.build()
            tool_output = message_to_string(
                self.llm.invoke(prompt=prompt, metadata=self.metadata)
            )

            response = excel_analyzer_bl.eval_expres(dframe=dataframe, hint=query, exp=tool_output.strip())
            analzye_prompt =self.generate_analyze_prompt(response= response, query=query)

            tool_output = message_to_string(
                self.llm.invoke(prompt=analzye_prompt, metadata=self.metadata)
            )

            yield ToolResponse(
                id=EXCEL_ANALYZER_RESPONSE_ID,
                response=tool_output
            )

    def generate_analyze_prompt(self, response, query):
        analzye_prompt = (
            f"Your data analyst, analyze the data from the dataframe and try to answer the user's question. "
        )

        stat_info = []
        if response.min_val is not None:
            stat_info.append("min")
        if response.max_val is not None:
            stat_info.append("max")

        if stat_info:
            analzye_prompt += f"You also have {', '.join(stat_info)}, average, and other statistical information. "
        else:
            analzye_prompt += "You have average and other statistical information. "

        analzye_prompt += (
            "Based on the statistics, provide useful insights. Write a detailed report based on the given data. "
            f"This is the user query: {query}. "
            f"Here are the facts: {response.data}"
        )

        if response.min_val is not None:
            analzye_prompt += f", min: {response.min_val}"

        if response.max_val is not None:
            analzye_prompt += f", max: {response.max_val}"

        return analzye_prompt

    def final_result(self, *args: ToolResponse) -> JSON_ro:
        tool_generation_response = cast(
            list[ToolResponse], args[0].response
        )
        # NOTE: need to do this json.loads(doc.json()) stuff because there are some
        # subfields that are not serializable by default (datetime)
        # this forces pydantic to make them JSON serializable for us
        return tool_generation_response
