from danswer.tools.infographics.exceptions import LLMException
from danswer.utils.logger import setup_logger
import json

logger = setup_logger()


def construct_prompt(dataframe):
    context = f"""Given the schema and sample data from a DataFrame, generate a set of insightful questions that can be used to further explore the data. The questions should be relevant to the columns, data types, and sample entries provided. 
                 Context:
                    - **DataFrame Schema:**
                      "{dataframe.dtypes}"
                    - **Sample Data:**
                        "{dataframe.head(10)}"
                 Instructions:
                     1. Review the DataFrame schema and sample data thoroughly.
                     2. Generate questions that can help a data analyst or scientist explore relationships, trends, anomalies, or patterns in the data.
                     3. Ensure that each question is directly relevant to the attributes and sample data provided.
                     4. Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative.
                     5. Strictly output the questions in the format: ['Question1?', 'Question2?', ...], where each question is a string enclosed in single quotes, starting with a capital letter and ending with a question mark.
                     6. Output only the list of questions without any additional text, headings, or explanations."""

    question = "Based on the DataFrame schema and sample data provided above, what are some insightful questions a data analyst can explore? Format your response as a list of strings, each string being a distinct question."
    prompt = f"""context: {context}, question: {question}"""
    logger.info(f'Prompt constructed: {prompt}')
    return prompt


class QuestionsRecommenderUsingLLM:
    def __init__(self, llm, llm_config, prompt_config):
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        logger.info(f'RecommendQuestionUsingLLM Instantiated')

    def recommend(self, dataframe, metadata=None):
        prompt = construct_prompt(dataframe)
        return self.invoke_llm(prompt=prompt, metadata=metadata)

    def invoke_llm(self, prompt, metadata=None):
        try:
            llm_response = self.llm.invoke(prompt=prompt, metadata=metadata)
            response = llm_response.content
            logger.info(f'LLM suggested questions: {response}')
            response = response.replace("'", '"').replace('\n', '')
            response = json.loads(response)
            # response = ["Draw chart for: " + element for element in response]
            logger.info(f'JSON formatted response : {response}')
            return response
        except Exception as e:
            logger.error(" QuestionsRecommenderUsingLLM.invoke_llm. Exception while Querying LLM: %s", str(e))
            raise LLMException(base_exception=e,
                               message="Exception while querying LLM: %s" % str(e))
