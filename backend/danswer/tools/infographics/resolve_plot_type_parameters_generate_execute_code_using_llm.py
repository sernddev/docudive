from dataclasses import dataclass

import pandas

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


def construct_prompt(sql_query, requirement, dataframe) -> str:
    """ Construct the detailed prompt for querying the LLM. """
    context = f"""
                    Context:
                    Given the SQL query results, user requirements, and dataframe, identify the best chart type for visualization using Plotly. 
                    Determine the appropriate parameters for the identified chart type and generate syntactically correct Python code to create the chart. 
                    The code should execute without errors using Python version 3.11.7 and Plotly version 5.5.0.

                    **SQL Query:**
                    {sql_query}

                    **Dataframe :**
                    {dataframe}

                    **User Requirements:**
                    {requirement}

                    Instructions:
                    1. Analyze the SQL query results and dataframe to identify the best chart type that fulfills the user requirements.
                    2. Determine the appropriate parameters (like 'x', 'y', 'color', and 'size') for the chosen chart type based on the dataframe and SQL query.
                    3. Generate only the line of code that creates the Plotly figure object 'fig', using the identified parameters and chart type. 
                    4. Ensure the code is syntactically correct for Python 3.17 and compatible with Plotly 5.5.0.
                    5. Ensure the parameters chosen are suitable for the identified chart type and focus on the visualization of user requirements.                 
                    6. The output should be solely the Python Plotly code necessary to generate the chart, with no additional explanations or text.
                    7. Output should be a single line of Python code for the Plotly chart without any data loading or DataFrame definition.  

                    Example Code Output:
                    ```python
                    fig = px.chart_type(df[df['gender'] == 'Female' & df['age'] < 30], x='identified_x_param', y='identified_y_param', color='identified_color_param', size_max=800)

            """

    question = (
        f"Based on the provided SQL query, dataframe, and user requirements, what is the appropriate chart type and parameters? "
        f"Generate the Python Plotly code required to create this chart.")
    prompt = f""" context: {context}, question: {question} """
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


class ResolvePlotTypeAndParametersAndGenerateExecuteCodeUsingLLM:

    def __init__(self, llm, llm_config: LLMConfig, prompt_config: PromptConfig):
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        logger.info('Initialized ResolvePlotParametersUsingLLM with model %s', self.llm_config.model_name)

    def resolve_graph_type_parameters_generate_execute_code(self, sql_query, requirement,
                                                            dataframe: pandas.DataFrame) -> list:
        """ Resolve graph parameters by querying the LLM with constructed prompts. """
        schema = format_dataframe_schema(dataframe.dtypes)
        prompt = construct_prompt(sql_query, requirement, dataframe)
        try:
            llm_response = self.llm.invoke(prompt=prompt)
            field_names = llm_response.content
            field_names = json.loads(field_names)
            print(f"field_names : {field_names}, type(field_names) = {type(field_names)}")
            logger.info('Fields resolved successfully')
            return field_names
        except Exception as e:
            logger.error("Failed to resolve graph parameters: %s", str(e))
            raise LLMException(base_exception=e,
                               message="Failed to resolve graph parameters for user requirement: %s" % str(requirement))


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
    resolver = ResolvePlotTypeAndParametersAndGenerateExecuteCodeUsingLLM(llm, llm_config, prompt_config)
    fields = resolver.resolve_graph_type_parameters_generate_execute_code(
        "SELECT * FROM Employees", "needs employee data analysis", "BAR")
    print(fields)