from langchain_core.messages import HumanMessage

TOOL_CALLING_PROMPT = """
Can you write the given input json: "{query}" into table format with columns and rows.

example: for given json format:
[
{{ "empid": 1,
  "lastname": "Adams",
  "firstname": "Andrew",
  "age": 18        
}},
{{ "empid": 2,
  "lastname": "James",
  "firstname": "kristen",
  "age": 24        
}}
]
    
output should be table format as:
 empid | lastname | firstname | age
 1 | Adams | Andrew | 18
 2 | James | kristen | age
     
"""


def build_sql_generation_user_prompt(
        query: str
) -> HumanMessage:

    return HumanMessage(
        content=TOOL_CALLING_PROMPT.format(query=query).strip()
    )
