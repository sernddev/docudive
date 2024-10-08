import json
from io import BytesIO

import pandas as pd
from tiktoken import Encoding

from danswer.file_processing.extract_file_text import get_file_ext
from danswer.file_store.models import InMemoryChatFile
from danswer.llm.utils import get_default_llm_tokenizer
from danswer.tools.tool import Tool
from danswer.utils.logger import setup_logger

OPEN_AI_TOOL_CALLING_MODELS = {"gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"}

logger = setup_logger()


def explicit_tool_calling_supported(model_provider: str, model_name: str) -> bool:
    if model_provider == "openai" and model_name in OPEN_AI_TOOL_CALLING_MODELS:
        return True

    return False


def compute_tool_tokens(tool: Tool, llm_tokenizer: Encoding | None = None) -> int:
    if not llm_tokenizer:
        llm_tokenizer = get_default_llm_tokenizer()
    return len(llm_tokenizer.encode(json.dumps(tool.tool_definition())))


def compute_all_tool_tokens(
    tools: list[Tool], llm_tokenizer: Encoding | None = None
) -> int:
    return sum(compute_tool_tokens(tool, llm_tokenizer) for tool in tools)


def generate_dataframe_from_excel( file:InMemoryChatFile):
        extension = get_file_ext(file.filename)
        content = file.content
        excel_byte_stream = BytesIO(content)
        excel_byte_stream.seek(0)
        if extension==".xlsx":
            dataframe = pd.read_excel(excel_byte_stream, engine="openpyxl")
            return dataframe
        elif extension == ".csv":
        # file = files[0]  # first file only

            dataframe = pd.read_csv(excel_byte_stream, quotechar='"', sep=',', escapechar='\\')
            return dataframe
        else:
          return  "Unsupported document file type. Supported document types include .csv and .xlsx "


def get_current_or_previous_files(files, history):
    fs = None
    if not files:
        logger.info('Searching for previous files in the history.')
        for previous_msg in history:
            if previous_msg.files:
                fs = previous_msg.files
                logger.info(f'Previous files found in the history: {fs}.')
                break
    else:
        logger.info(f'Current files found: {files}')
        fs = files
    return fs


def load_to_dataframe(content):
    excel_byte_stream = BytesIO(content)
    dataframe = pd.read_csv(excel_byte_stream)
    logger.info(f'Content loaded to the dataframe : \n{dataframe.dtypes}\n')
    return dataframe
