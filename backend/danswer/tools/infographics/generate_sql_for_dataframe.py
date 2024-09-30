from dataclasses import dataclass

from danswer.tools.excel.excel_analyzer_tool import TASK_PROMPT
from danswer.tools.infographics.exceptions import LLMException
from danswer.tools.questions_recommender.exceptions import PromptGenerationException
from danswer.utils.logger import setup_logger
import json
import re

# Setup logger
logger = setup_logger()

SYSTEM_PROMPT = """Generate an syntactically correct SQLite query based on the provided SQL schema and user requirement. 
                    Always return syntactically correct SQLite query, don't provide any explanation"""


TASK_PROMPT = """Guidelines:
                - Use standard SQLite syntax.
                - Ensure the query accurately meets the user's specified requirement.
                - Ensure that columns names/alias names in SQLite query is same as dataframe schema column names.
                - Always use the table name df in your query.
                - Incorporate case-insensitive comparisons for string values to accommodate potential case variations in the data.                                                
                - Do not include any explanations or additional text.
                - Output just SQLite Query."""


@dataclass
class LLMConfig:
    model_name: str
    other_configurations: dict


@dataclass
class PromptConfig:
    template: str


def post_process(text):
    return "".join([json.loads(token)['response'] for token in text['text'].strip().split('\n')])


def format_dataframe_schema(dtypes):
    # Mapping of pandas dtypes to SQL data types
    dtype_map = {
        'int64': 'INT',
        'float64': 'FLOAT',
        'object': 'VARCHAR',  # Assuming 'object' type is used for strings
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'DATE',
        # Add other necessary mappings based on your dtypes
    }

    # Build schema string
    schema_lines = []
    for column, dtype in dtypes.items():
        # Map pandas dtype to SQL type
        sql_type = dtype_map.get(str(dtype), 'VARCHAR')  # Default to VARCHAR if unknown
        # Append formatted column specification
        schema_lines.append(f"{column} : {sql_type}")

    # Join all lines with commas and newlines
    schema = ",\n".join(schema_lines)
    return f"\"\"\"\n{schema}\n\"\"\""


def extract_sql(text):
    pattern = r'```(.*?)```'
    # Using re.DOTALL to make '.' match newlines as well
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = match.group(1).strip()  # Remove leading/trailing whitespace
        print("Extracted SQL Query:", text)
    else:
        print("No SQL query found.")
    return text


def construct_prompt_from_requirements_and_previous_data(schema, requirement, previous_sql_queries,
                                                         previous_response_errors):
    """ Construct the detailed prompt for querying the LLM. """
    schema = format_dataframe_schema(schema)
    # Check if there are entries in previous SQL queries or response errors and format them accordingly
    previous_queries_section = (
        f"{previous_sql_queries} "
        if previous_sql_queries else ""
    )

    previous_errors_section = (
        f"{previous_response_errors} "
        if previous_response_errors else ""
    )

    error_handling_section = (
        f"**Previously Incorrect SQL Query**:\n{previous_queries_section}\n **Previous Response Errors ** :\n{previous_errors_section}\n"
        "Ensure the new SQL query corrects these errors and adheres to the correct SQLite syntax."
    )

    # Construct the full prompt with conditional sections included
    generate_sql = (
        f"{SYSTEM_PROMPT} "
        f"{error_handling_section}\n"
        f"** DataFrame Schema: **\n{schema}\n"
        f"** User Requirements: **\n{requirement}\n"
        f"{TASK_PROMPT}"
    )

    question = "Generate a correct and error-free SQL Query for SQLite, correcting the errors from previous attempts based on the provided schema and requirements."

    df_prompt = f""" context: {generate_sql}, question: {question} """

    return df_prompt


def construct_prompt_from_requirements(schema, requirement, table_name='df'):
    """ Construct the detailed prompt for querying the LLM. """
    try:
        schema = format_dataframe_schema(schema)
        generate_sql = (f"{SYSTEM_PROMPT} \n"
                        f"** DataFrame Schema: **\n {schema} \n "
                        f"** User Requirements: **\n {requirement} \n "
                        f"{TASK_PROMPT}")
        question = f"Generate SQL Query based on the provided context, schema, data and user requirements."
        sql_prompt = f""" context: {generate_sql}, question: {question} """
    except Exception as e:
        logger.error(f'Exception encountered while generating prompt for sql generation: {e}')
        raise PromptGenerationException(base_exception=e, message=str('Exception encountered while generating prompt for sql generation. '
                                                                      'Try correcting the prompt.'))
    return sql_prompt


class GenerateSqlForDataframe:
    def __init__(self, llm, llm_config: LLMConfig, prompt_config: PromptConfig):
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        logger.info('Initialized GenerateSqlForDataframe with model %s', self.llm_config.model_name)

    def generate_sql_query(self, schema, requirement, previous_sql_queries=None, previous_response_errors=None,
                           metadata=None) -> list:
        """ Generate SQL Query by querying the LLM with constructed prompts. """
        if previous_response_errors and previous_sql_queries:
            prompt = construct_prompt_from_requirements_and_previous_data(schema, requirement,
                                                                               previous_sql_queries,
                                                                               previous_response_errors)
        else:
            prompt = construct_prompt_from_requirements(schema, requirement)

        try:
            llm_response = self.llm.invoke(prompt=prompt, metadata=metadata)
            sql_query = llm_response.content
            if sql_query:
                sql_query = extract_sql(sql_query)
            logger.info(
                f'SQL Query generated successfully. SQL Query : {sql_query}, type(field_names) = {type(sql_query)}')
            return sql_query
        except Exception as e:
            logger.error("Failed to generate SQL Query: %s", str(e))
            raise LLMException(e, f"Exception received during generate_sql_query : {str(e)}")


if __name__ == '__main__':
    llm_config = LLMConfig(model_name="model_v1", other_configurations={})
    prompt_config = PromptConfig(
        template="""Given the SQL query results, database schema, and user requirements, please suggest appropriate fields for creating a visualization using Plotly...""")


    # Mocking llm.invoke for demonstration
    class MockLLM:
        def invoke(self, prompt):
            class Response:
                content = ['dept_name', 'hire_date', 'employee_count']

            return Response()


    llm = MockLLM()
    resolver = GenerateSqlForDataframe(llm, llm_config, prompt_config)
    fields = resolver.generate_sql_query(
        "SELECT * FROM Employees", "needs employee data analysis", "BAR")
    print(fields)
