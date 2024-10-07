import json
from collections.abc import Generator
from typing import Any
from typing import cast

import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session

from danswer.dynamic_configs.interface import JSON_ro
from danswer.file_store.models import InMemoryChatFile
from danswer.llm.answering.prompts.build import AnswerPromptBuilder, \
    default_build_system_message_by_prmpt, default_build_user_message_by_task_prompt
from danswer.llm.utils import message_to_string, check_number_of_tokens
from danswer.tools.excel import excel_analyzer_bl
from danswer.tools.excel.excel_analyzer_bl import load_and_convert_types, dataframe_to_markdown_bold_header
from danswer.tools.tool import Tool
from danswer.tools.tool import ToolResponse
from danswer.tools.utils import generate_dataframe_from_excel
from danswer.utils.logger import setup_logger
from danswer.db.models import Persona, ChatMessage
from danswer.db.models import User
from danswer.llm.answering.models import PromptConfig, PreviousMessage
from danswer.llm.interfaces import LLMConfig, LLM

logger = setup_logger()

detailed_keywords = [
    "detailed report", "in-depth analysis", "comprehensive", "full report", "elaborate",  # English
    "تقرير مفصل", "تحليل متعمق", "شامل", "تقرير كامل", "موسع"  # Arabic
]

concise_keywords = [
    "concise summary", "brief", "summary", "short report", "quick overview",  # English
    "ملخص موجز", "موجز", "ملخص", "تقرير قصير", "نظرة سريعة"  # Arabic
]

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
        # rephrased_query = history_based_query_rephrase(query=query, history=history, llm=llm)
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
        if query.startswith("Draw chart for:"):
            query = query[len("Draw chart for:"):]
        query = query.strip()
        file = None
        if self.files is not None and len(self.files) > 0:
            file = self.files[0]
        elif self.history is not None and len(self.history) > 0:
            previous_msgs = self.history[0]
            if previous_msgs.files is not None and len(previous_msgs.files) > 0:
                file = previous_msgs.files[0]
        else:
            file = None  # Handle case where no file is found

        if file:
            dataframe = generate_dataframe_from_excel(file)
            if not isinstance(dataframe, pd.DataFrame):
                return dataframe

            dataframe = load_and_convert_types(dataframe)

            quer_with_schema = self.get_schema_with_prompt(dataframe, query)
            # send query to LLM to get pandas functions, out put should be valid pandas function
            # we don't need to send file content to LLM, becz it is structure data loaded to dataframe
            for f in self.history: f.files = []

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
            self.log_response_data(response)
            analzye_prompt = self.generate_analyze_prompt(response=response, query=query, schema=quer_with_schema,
                                                          original_dataset=dataframe)

            tool_output = message_to_string(
                self.llm.invoke(prompt=analzye_prompt, metadata=self.metadata)
            )
            if response.data is None and not response.has_min_max():
                tool_output += f"\n\nData Preview : \n\n{dataframe_to_markdown_bold_header(dataframe.head(5))}"

            if isinstance(response.data, pd.DataFrame):
                tool_output += f"\n\nResults : \n\n{dataframe_to_markdown_bold_header(response.data.head(10))}"

            yield ToolResponse(
                id=EXCEL_ANALYZER_RESPONSE_ID,
                response=tool_output
            )

        yield ToolResponse(
            id=EXCEL_ANALYZER_RESPONSE_ID,
            response="Please upload file"
        )

    def log_response_data(self, response):
        data = response.data

        if isinstance(data, pd.DataFrame):
            # Temporarily set Pandas to display all columns
            pd.set_option('display.max_columns', None)

            # Log the DataFrame details, ensuring all columns are visible
            logger.info(f"eval response with {len(data)} rows and {len(data.columns)} columns:\n{data}")

            # Optionally reset the display settings to avoid affecting other code
            pd.reset_option('display.max_columns')
        else:
            # Log the response data directly for non-DataFrame types
            logger.info(f"eval response data: {data}")

    def get_schema_with_prompt(self, dataframe, query):
        with pd.option_context('display.max_columns', None):
            quer_with_schema = (
                    "dataframe schema with fields: \n"
                    + str(dataframe.dtypes)
                    + "\n\n"
                    + "sample data: \n"
                    + str(dataframe.head(5))
                    + f"\nuser query: {query}"
            )

        return quer_with_schema

    def identify_report_type(self, query):
        '''
        this can be replaced with LLM cal to identify request type
        :param query:
        :return:
        '''
        if any(keyword in query for keyword in detailed_keywords):
            return "detailed"
        elif any(keyword in query for keyword in concise_keywords):
            return "concise"
        else:
            return "concise"

    def get_dataframe_preview(self, dataframe):
        # return f"{dataframe_to_markdown_bold_header(dataframe.head(10))}"
        # return f"{dataframe.head(5).to_json(orient='records')}"
        return f"{dataframe.to_csv(index=False, header=True)}"

    def generate_analyze_prompt(self, response, query, schema, original_dataset: pd.DataFrame):

        analzye_prompt = (
            f"Your data analyst, analyze the data from the dataframe and try to answer the user's question. "
        )

        if ((response.data is None and not response.has_min_max()) or
                (isinstance(response.data, pd.DataFrame) and len(response.data) == 0)):
            analzye_prompt = (
                f"This is the user query: {query}. "
                "No valid data was fetched. Please ask user to re-write the question, make this very short and "
                "meaning full in separate paragraph, mention based on given data."
                f"suggest 3 very simple text question based on the  schema like with where clause or group by (but "
                f"dont tell user these are simple questions),"
                f"dont generate any source code,  just generate questions  based on this schema:{schema}, "
                f"and ask user to try"
                f"\n\n Data Preview in csv format: {self.get_dataframe_preview(original_dataset.head(5))},"
            )
            return analzye_prompt

        if response.has_min_max() is not False and "detailed" in self.identify_report_type(query):
            analzye_prompt += f", Statistics information :  {str(response.stats_info)}"
        elif response.has_min_max() is not False:
            analzye_prompt += f", min: {response.stats_info['min']} , max: {response.stats_info['max']}"

        if response.data is not None:
            temp_data = None
            type_of_data = None

            # Determine the type of data
            if isinstance(response.data, pd.DataFrame):
                type_of_data = 'dataframe'
                if len(response.data) > 10:
                    # temp_data = (f"\n\n ''' {self.get_dataframe_preview(response.data.head(5))} '''"
                    temp_data = (f" \n\nInform user your displaying only few records matches for the given query., "
                                 f"total records for the query is: {len(response.data)}")
                else:
                    temp_data = response.data
            elif isinstance(response.data, pd.Series):
                type_of_data = 'series'
                temp_data = (
                    f"\n\n Inform user, this is small set of data, full data is not included in report"
                    f"\n\nTotal records for the query is: {len(response.data)}")
            else:
                type_of_data = 'single_value'
                temp_data = str(response.data)

            report_text = (
                "\nBased on the given statistical data, provide useful insights. Write a detailed report based on the "
                "given data." if "detailed" in self.identify_report_type(query)
                else "\nBased on the given statistical data, provide a concise summary on the given data. Don't explain "
                     "much."
            )

            if type_of_data == 'dataframe':
                analzye_prompt += (
                    f"{report_text} "
                    f"User query: {query}. "
                    f"\nTotal record count for the user query: {len(response.data)} out of total records in given data {len(original_dataset)}."
                    f"\nResponse for user query (in csv format): \n{temp_data}"
                )
            elif type_of_data == 'series':
                analzye_prompt += (
                    f"{report_text} "
                    f"This is the user query: {query}. "
                    f"Answer for user query: \n{temp_data}"
                )
            elif type_of_data == 'single_value':
                analzye_prompt += (
                    f"{report_text} "
                    f"This is the user query: {query}. "
                    f"Answer for user query: {temp_data}"
                )

        logger.info(analzye_prompt)

        analzye_prompt = analzye_prompt + ("\n\n DON'T MENTION THAT YOUR USING DATAFRAME, WHEN EVER REQUIRED SAY BASED "
                                           "ON GIVEN DATA OR DATASET. DON'T USE YOUR OWN KNOWLEDGE TO PROVIDE ANSWER, "
                                           "PLEASE USE GIVEN CONTEXT ONLY")
        return analzye_prompt

    def final_result(self, *args: ToolResponse) -> JSON_ro:
        tool_generation_response = cast(
            list[ToolResponse], args[0].response
        )
        # NOTE: need to do this json.loads(doc.json()) stuff because there are some
        # subfields that are not serializable by default (datetime)
        # this forces pydantic to make them JSON serializable for us
        return tool_generation_response
