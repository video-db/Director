import os
import json

from director.llm.openai import OpenAIChatModel

from enum import Enum


class ToolsType(str, Enum):
    apps = "apps"
    actions = "actions"

def composio_tool(task: str, auth_data: dict = None, tools_type:ToolsType=ToolsType.apps):
    from composio_openai import ComposioToolSet
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.openai.com/v1"

    if not key:
        key = os.getenv("VIDEO_DB_API_KEY")
        base_url = os.getenv("VIDEO_DB_BASE_URL", "https://api.videodb.io")

    openai_client = OpenAI(api_key=key, base_url=base_url)

    toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"))

    if auth_data and "name" in auth_data and "token" in auth_data:
        toolset.add_auth(
            app=auth_data["name"].upper(),
            parameters=[
                {
                    "name": "Authorization",
                    "in_": "header",
                    "value": f"Bearer {auth_data['token']}"
                }
            ]
        )

    if tools_type == ToolsType.apps:
        tools = toolset.get_tools(apps=os.getenv("COMPOSIO_APPS"))

    elif tools_type == ToolsType.actions:
        tools = toolset.get_tools(actions=os.getenv("COMPOSIO_ACTIONS"))


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
