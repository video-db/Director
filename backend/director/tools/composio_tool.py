import os
import json

from director.llm.openai import OpenAIChatModel


def composio_tool(task: str):
    from composio_openai import ComposioToolSet
    from openai import OpenAI

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"))
    tools = toolset.get_tools(apps=json.loads(os.getenv("COMPOSIO_APPS")))
    print(tools)

    response = openai_client.chat.completions.create(
        model=OpenAIChatModel.GPT4o,
        tools=tools,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": task},
        ],
    )

    composio_response = toolset.handle_tool_calls(response=response)
    if composio_response:
        return composio_response
    else:
        return response.choices[0].message.content or ""
