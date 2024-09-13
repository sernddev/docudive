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


def construct_prompt(sql_query, schema, requirement, chart_type):
    resolve_x_and_y_context = f"""**SQL Query Results and Schema Context:**
        Given the SQL query results and database schema, identify the appropriate fields for creating a visualization using Plotly. The output should directly match the SQL query structure, considering all selected fields.

        **SQL Query:**
        {sql_query}

        **Database Schema:**
        {schema}

        **Chart Type:**
        {chart_type}

        **User Requirements:**
        {requirement}    
        \n The user aims to visualize data related to the SQL query focused on requirement, requiring a comprehensive representation of all fields used in the SQL query for aggregations, computations, or groupings.\n    

        **Expected Fields from SQL Query:**
        - Ensure that the number of fields suggested corresponds exactly to the number of columns returned by the SQL query.
        - The fields should be listed in the order they appear in the SQL query results and presented in a dictionary format appropriate to the chart type.    

        **Guidelines for Suggesting Fields:**
        - For PIE, BAR, and HEATMAP charts, suggest fields for 'x' and 'y' and return dictionary like {{"x": "", "y": ""}}.
        - For SCATTER charts, suggest fields for 'x', 'y', and 'color' and return dictionary like {{"x": "", "y": "", "color": ""}}.
        - For SCATTER_MATRIX charts, suggest fields for 'x', 'y', 'color', and 'size' and return dictionary like {{"x": "", "y": "", "color": "", "size": ""}}.         
        - Ensure the 'size' parameter must be a numeric field; if the initially suggested 'size' is not numeric, suggest the next available numeric field from the database.
        - If no suitable numeric field is available for 'size', reconsider the roles of 'x' and 'y' to ensure they are optimally assigned.
        - Analyze columns properly to suggest the right match for each parameter, especially for SCATTER_MATRIX:
          - 'x' and 'y' should be chosen based on their ability to represent dimensions.
          - 'color' should ideally be a categorical variable.
          - 'size' must be a numeric column, suitable for quantifying or scaling markers.
        - Avoid assumptions; ensure the suggested fields match the actual data types required for each chart parameter.
        - Do not include any explanations or additional text.

        **Output:**
        Provide suggestions in a dictionary format, ensuring all suggestions align with the type of visualization to effectively convey the intended insights and reflect the data structure accurately.
        """
    question = f"Based on the SQL Query and user requirements, what are the appropriate field names for plotting a {chart_type}? Please format your response as a dictionary mapping field names to the roles they play in the visualization."
    prompt = f""" context: {resolve_x_and_y_context}, question: {question} """
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
                                 chart_type, metadata=None) -> list:
        """ Resolve graph parameters by querying the LLM with constructed prompts. """
        prompt = construct_prompt(sql_query, format_dataframe_schema(schema), requirement, chart_type)
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
