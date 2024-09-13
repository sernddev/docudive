from danswer.tools.infographics.dataframe_inmemory_sql import DataframeInMemorySQL
from danswer.tools.infographics.exceptions import DataframeInMemorySQLExecutionException
from danswer.tools.infographics.generate_sql_for_dataframe import GenerateSqlForDataframe
from danswer.tools.infographics.resolve_plot_parameters_using_llm import ResolvePlotParametersUsingLLM, LLMException
from danswer.tools.infographics.plot_charts import generate_chart_and_save, find_chart_type
from danswer.tools.infographics.resolve_plot_type_parameters_generate_execute_code_using_llm import \
    ResolvePlotTypeAndParametersAndGenerateExecuteCodeUsingLLM
from danswer.tools.utils import load_to_dataframe
from danswer.utils.logger import setup_logger

logger = setup_logger()


class PlotSummarizeGenerateSQL:
    def __init__(self, llm, llm_config, prompt_config):
        self.dataframe_inmemory_sql = None
        logger.info(f'Instantiating ChartSummarizeGenerateSQL')
        self.llm = llm
        self.llm_config = llm_config
        self.prompt_config = prompt_config
        self.allowed_attempt = 3
        self.resolve_plot_parameters = ResolvePlotParametersUsingLLM(llm=llm,
                                                                     llm_config=llm_config,
                                                                     prompt_config=prompt_config)
        self.generate_sql_for_dataframe = GenerateSqlForDataframe(llm=llm,
                                                                  llm_config=llm_config,
                                                                  prompt_config=prompt_config)
        self.generate_chart = ResolvePlotTypeAndParametersAndGenerateExecuteCodeUsingLLM(llm=llm,
                                                                                         llm_config=llm_config,
                                                                                         prompt_config=prompt_config)

    def generate_execute_sql_dataframe(self, file, query, metadata) -> tuple:
        dataframe = load_to_dataframe(file.content)
        return self.generate_execute_self_correct_sql(dataframe, query, metadata)

    def generate_execute_self_correct_sql(self, dataframe, query, metadata):
        filtered_df = None
        sql_query = None
        if not dataframe.empty:
            previous_sqls = []
            previous_errors = []
            current_attempt = 1
            while current_attempt <= self.allowed_attempt:
                try:
                    logger.info(f"Attempt #{current_attempt}. generate_execute_dataframe_sql")
                    sql_query = self.generate_sql_for_dataframe.generate_sql_query(schema=dataframe.dtypes,
                                                                                   requirement=query,
                                                                                   previous_sql_queries=previous_sqls,
                                                                                   previous_response_errors=previous_errors,
                                                                                   metadata=metadata)
                    filtered_df = self.execute_sql_on_dataframe(df=dataframe, sql_query=sql_query)
                    logger.info(
                        f'\n******************* filtered_df received *******************: \n{filtered_df.info}\n************************************************************')
                    if filtered_df is None or filtered_df.empty:
                        raise DataframeInMemorySQLExecutionException(ValueError("ResultSet after executing SQL query is of size 0."),
                                                                     "SQL query resulted in no data.")
                    break
                except (DataframeInMemorySQLExecutionException, LLMException) as e:
                    logger.error(f'Exception received while executing generate_execute_self_correct_sql: {str(e)}')
                    previous_response = str(e.base_exception)
                    previous_sqls.append(sql_query)
                    previous_errors.append(previous_response)
                    current_attempt += 1
                    filtered_df = None
                    if current_attempt > self.allowed_attempt:
                        raise e
        return dataframe, filtered_df, sql_query

    def resolve_chart_type_and_parameters_and_generate_and_execute_python_code(self, filtered_df, sql_query,
                                                                               user_requirement, metadata=None) -> str:
        if filtered_df is not None and not filtered_df.empty:
            try:
                self.generate_chart.resolve_graph_type_parameters_generate_execute_code(sql_query=sql_query,
                                                                                        requirement=user_requirement,
                                                                                        dataframe=filtered_df)
            except LLMException as e:
                logger.error(f'Exception while resolve_parameters_and_generate_chart: {str(e)}')
                return f'Exception while resolve_parameters_and_generate_chart: {str(e)}'
        else:
            return 'Failed To resolve parameters and generate chart. Dataframe is empty.'

    def resolve_parameters_and_generate_chart(self, filtered_df, sql_query, user_requirement, metadata=None) -> str:
        if filtered_df is not None and not filtered_df.empty:
            try:
                chart_type = find_chart_type(filtered_df)
                column_names = self.resolve_plot_parameters.resolve_graph_parameters(sql_query=sql_query,
                                                                                     schema=filtered_df.dtypes,
                                                                                     requirement=user_requirement,
                                                                                     chart_type=chart_type,
                                                                                     metadata=metadata)
                # TODO: check resolved params name are same as column name
                image_url = generate_chart_and_save(dataframe=filtered_df,
                                                    field_names=column_names,
                                                    chart_type=chart_type)
                logger.info(f'image_path generated successfully: {image_url}')
                return image_url
            except LLMException as e:
                logger.error(f'Exception while resolve_parameters_and_generate_chart: {str(e)}')
                return f'Exception while resolve_parameters_and_generate_chart: {str(e)}'
        else:
            return 'Failed To resolve parameters and generate chart. Dataframe is empty.'

    def execute_sql_on_dataframe(self, df, sql_query):
        # execute query on dataframe
        self.dataframe_inmemory_sql = DataframeInMemorySQL(df=df)
        try:
            filtered_df = self.dataframe_inmemory_sql.execute_sql(sql_query)
            logger.info(f'dataframe_in_memory_sql df: {filtered_df}')
        except (DataframeInMemorySQLExecutionException, Exception) as e:
            logger.error(f'dataframe_in_memory_sql exception: {e}')
            raise DataframeInMemorySQLExecutionException(e, "No rows fetched after executing SQL Query. "
                                                            "SQL generated may not be correct. Try rephrasing the query."
                                                            "Exception while executing execute_sql_on_dataframe()")
        return filtered_df
