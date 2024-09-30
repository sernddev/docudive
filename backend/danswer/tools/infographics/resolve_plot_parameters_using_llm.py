from dataclasses import dataclass
from danswer.tools.infographics.exceptions import LLMException
from danswer.utils.logger import setup_logger
import json

# Setup logger
logger = setup_logger()


@dataclass
class LLMConfig:
    model_name: str
    other_configurations: dict


@dataclass
class PromptConfig:
    template: str


def construct_prompt(sql_query, schema, requirement, chart_type, prompt_config):
    system_prompt = prompt_config.system_prompt
    system_prompt = system_prompt.format(sql_query=sql_query, schema=schema, chart_type=chart_type, requirement=requirement)
    task_prompt = prompt_config.task_prompt
    context = system_prompt + "\n\n" + task_prompt
    question = (f"Based on the sql query, schema, chart and user requirements, what are the appropriate field names for plotting a {chart_type}? "
                f"Please format your response as a dictionary mapping field names to the roles they play in the visualization.")
    prompt_template = f""" context: {context}, question: {question} """
    prompt = prompt_template.format(context=context, question=question)
    return prompt


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


class ResolvePlotParametersUsingLLM:

    def __init__(self, llm, llm_config: LLMConfig, prompt_config: PromptConfig):
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        logger.info('Initialized ResolvePlotParametersUsingLLM with model %s', self.llm_config.model_name)

    def resolve_graph_parameters(self, sql_query, schema, requirement,
                                 chart_type, metadata=None, prompt_config: PromptConfig = None) -> list:
        """ Resolve graph parameters by querying the LLM with constructed prompts. """
        prompt = construct_prompt(sql_query, format_dataframe_schema(schema), requirement, chart_type, prompt_config)
        try:
            llm_response = self.llm.invoke(prompt=prompt, metadata=metadata)
            field_names = llm_response.content
            field_names = json.loads(field_names)
            logger.info(f'Fields resolved successfully. field_names : {field_names}, type(field_names) = {type(field_names)}')
            return field_names
        except Exception as e:
            logger.error("Failed to resolve graph parameters: %s", str(e))
            raise LLMException(base_exception=e, message="Failed to resolve graph parameters for user requirement: %s" % str(requirement))


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
    resolver = ResolvePlotParametersUsingLLM(llm, llm_config, prompt_config)
    fields = resolver.resolve_graph_parameters(
        "SELECT * FROM Employees", "needs employee data analysis", "BAR")
    print(fields)
