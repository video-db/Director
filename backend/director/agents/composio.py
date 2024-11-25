import os
import logging
import json

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    ContextMessage,
    RoleTypes,
    TextContent,
    MsgStatus,
)

from director.tools.composio_tool import composio_tool
from director.llm import get_default_llm
from director.llm.base import LLMResponseStatus

logger = logging.getLogger(__name__)

COMPOSIO_PARAMETERS = {
    "type": "object",
    "properties": {
        "task": {
            "type": "string",
            "description": "The task to perform",
        },
    },
    "required": ["task"],
}


class ComposioAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "composio"
        self.description = f'The Composio agent is used to run tasks related to apps like {os.getenv("COMPOSIO_APPS")} '
        self.parameters = COMPOSIO_PARAMETERS
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)

    def run(self, task: str, *args, **kwargs) -> AgentResponse:
        """
        Run the composio with the given task.

        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            self.output_message.actions.append("Running task..")
            self.output_message.push_update()

            text_content = TextContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Running task..",
            )
            self.output_message.content.append(text_content)
            self.output_message.push_update()

            composio_response = composio_tool(task=task)
            llm_prompt = (
                f"User has asked to run a task: {task} in Composio. \n"
                "Format the following reponse into text.\n"
                "Give the output which can be directly send to use \n"
                "Don't add any extra text \n"
                f"{json.dumps(composio_response)}"
            )
            composio_response = ContextMessage(content=llm_prompt, role=RoleTypes.user)
            llm_response = self.llm.chat_completions([composio_response.to_llm_msg()])
            if llm_response.status == LLMResponseStatus.ERROR:
                raise Exception(f"LLM Failed with error {llm_response.content}")

            text_content.text = llm_response.content
            text_content.status = MsgStatus.success
            text_content.status_message = "Here is the response from Composio"

        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            text_content.status = MsgStatus.error
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={"composio_response": composio_response},
        )
