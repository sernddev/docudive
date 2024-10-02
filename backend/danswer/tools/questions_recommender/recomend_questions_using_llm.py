from dataclasses import dataclass
from danswer.tools.infographics.exceptions import LLMException
from danswer.tools.questions_recommender.exceptions import PromptGenerationException
from danswer.utils.logger import setup_logger
import json
import pandas as pd


logger = setup_logger()

CONTEXT_TEMPLATE = '''
        Given the input, whether it's structured data (e.g., a DataFrame) or unstructured content (e.g., a PDF or text file), 
        generate a set of insightful questions that can be used to further explore the information provided. 
        The questions should be relevant to the key themes, concepts, entities, or data points present in the input.

        Context:
        - **Data Input:**
            {data_input}

        Instructions:
        1. Review the provided input thoroughly, whether it is structured (e.g., DataFrame schema and sample data) or unstructured (e.g., text, PDF).
        2. Generate questions that help a researcher, analyst, or scientist explore relationships, trends, anomalies, or patterns within the input.
        3. Ensure that each question is directly relevant to the information presented in the input.
        4. For structured data (DataFrame):
           - Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative, etc.

           For unstructured content (Text or PDF):
           - Questions may relate to key themes, potential inconsistencies, missing information, or areas that require further exploration, etc.

        5. Strictly output the questions in the format: ["Question1?", "Question2?", ...], where each question is a string enclosed in double quotes, starting with a capital letter and ending with a question mark.
        6. The output must be a valid JSON array of strings, without any additional text, headings, or explanations.
        7. Do not include any additional text, headings, or explanations in response.        
        '''

RESPONSE_START_STR = 'Here are the questions that can be used to further explore the information provided:'


@dataclass
class PromptConfig:
    system_prompt: str
    task_prompt: str


def generate_prompt(prompt_config: PromptConfig, schema: pd.DataFrame.dtypes = None, structured_data=None, unstructured_data: str = None):
    context_template = prompt_config.system_prompt + " " + prompt_config.task_prompt
    try:
        if schema is not None and structured_data is not None:
            # Sample inputs for structured and unstructured scenarios
            data_input = f"- **Structured Data (DataFrame):**\n  - Schema: \"{schema}\"\n  - Sample Data: \"{structured_data}\""
        elif unstructured_data:
            data_input = f"- **Unstructured Data (Document Excerpt):**\n  - \"{unstructured_data}\""
        else:
            raise PromptGenerationException(message="Exception occurred while generating the prompt."
                                                    "Either structured data or unstructured data must be provided.")
        context = context_template.format(data_input=data_input)
        question = '\n\nPlease read the context and instructions very carefully and answer precisely in the expected output format with no additional texts.\n\n'
        prompt_template = f"""context: {context}, question: {question}"""
        prompt = prompt_template.format(context=context, question=question)
        logger.info(f'prompt: {prompt}')
        return prompt
    except Exception as e:
        raise PromptGenerationException(base_exception=e, message="Exception occurred while generating the prompt. "
                                                                  "Please check and modify the prompt.")


def generate_default_prompt(schema: pd.DataFrame.dtypes = None, structured_data=None, unstructured_data: str = None):
    try:
        if schema is not None and structured_data is not None:
            # Sample inputs for structured and unstructured scenarios
            data_input = f"- **Structured Data (DataFrame):**\n  - Schema: \"{schema}\"\n  - Sample Data: \"{structured_data}\""
        elif unstructured_data:
            data_input = f"- **Unstructured Data (Document Excerpt):**\n  - \"{unstructured_data}\""
        else:
            raise PromptGenerationException(message="Exception occurred while generating the prompt."
                                                    "Either structured data or unstructured data must be provided.")
        context = CONTEXT_TEMPLATE.format(data_input=data_input)
        question = '\n\n\n\nPlease read the context carefully and answer precisely in the expected output format with no additional texts.\n\n'
        prompt_template = f"""context: {context}, question: {question}"""
        prompt = prompt_template.format(context=context, question=question)
        logger.info(f'prompt: {prompt}')
        return prompt
    except Exception as e:
        raise PromptGenerationException(base_exception=e, message="Exception occurred while generating the prompt. "
                                                                  "Please check and modify the prompt.")


class QuestionsRecommenderUsingLLM:
    def __init__(self, llm, llm_config, prompt_config: PromptConfig):
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        logger.info(f'RecommendQuestionUsingLLM Instantiated')

    def recommend(self, dataframe: pd.DataFrame, metadata=None):
        if self.prompt_config:
            prompt = generate_prompt(self.prompt_config, schema=dataframe.dtypes, structured_data=dataframe.head(10), unstructured_data=None)
        else:
            prompt = generate_default_prompt(dataframe)
        return self.invoke_llm(prompt=prompt, metadata=metadata)

    def recommend_for_unstructured_data(self, text: str, metadata=None):
        prompt = generate_prompt(self.prompt_config, schema=None, structured_data=None, unstructured_data=text)
        response = self.invoke_llm(prompt=prompt, metadata=metadata)
        logger.info(f'Recommended questions for Unstructured data : {response}')
        return response

    def invoke_llm(self, prompt: str, metadata=None):
        try:
            llm_response = self.llm.invoke(prompt=prompt, metadata=metadata)
            response = llm_response.content
            logger.info(f'LLM suggested questions: {response}')
            if RESPONSE_START_STR in response:
                response = response[len(RESPONSE_START_STR):]
            if '\n' in response:
                response = response.replace('\n', '')
            response = json.loads(response)
            logger.info(f'JSON formatted response : {response}')
            return response
        except Exception as e:
            logger.error(" QuestionsRecommenderUsingLLM.invoke_llm. Exception while Querying LLM: %s", str(e))
            raise LLMException(base_exception=e,
                               message="Exception while querying LLM: %s" % str(e))


if __name__ == '__main__':
    header = ['col1', 'col1', 'col3', 'col4', 'col5']
    rows = [[1,2,3,4,5], [6,7,8,9,0], [1,2,3,4,5], [2,3,4,7,6], [3,54,5,2,5]]
    df = pd.DataFrame(columns=header, data=rows)
    print(df)
    schema_input = df.dtypes
    data_input = df.head()
    system = f"""Given the schema and sample data from a DataFrame, generate a set of insightful questions that can be used to further explore the data. 
        The questions should be relevant to the columns, data types, and sample entries provided.

        Context:
        - **DataFrame Schema:**
          "{schema_input}"
        - **Sample Data:**
          "{data_input}"
    """
    task = """
            Instructions:
                1. Review the DataFrame schema and sample data thoroughly.
                2. Generate questions that can help a data analyst or scientist explore relationships, trends, anomalies, or patterns in the data.
                3. Ensure that each question is directly relevant to the attributes and sample data provided.
                4. Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative.
                5. Strictly output the questions in the format: ['Question1?', 'Question2?', ...], where each question is a string enclosed in single quotes, starting with a capital letter and ending with a question mark.
                6. Output only the list of questions without any additional text, headings, or explanations.                
                Based on the DataFrame schema and sample data provided above, what are some insightful questions a data analyst can explore? Format your response as a list of strings, each string being a distinct question.
        """
    # prompt = generate_prompt(system, task, schema_input, data_input)
    # prompt = construct_default_prompt(dataframe=df)
    text = '''Some random text <..........>'''
    prompt = generate_prompt(schema=df.dtypes, structured_data=data_input, unstructured_data=text)
    print(f'prompt: {prompt}')
    prompt = generate_prompt(schema=None, structured_data=None, unstructured_data=text)
    print(f'prompt: {prompt}')