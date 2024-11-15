import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, TextContent

from director.tools.composio_tool import composio_tool

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
        self.description = (
            "The Composio agent is used to generate responses using the Composio tool."
        )
        self.parameters = COMPOSIO_PARAMETERS
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

            composio_response = composio_tool(task=task)

        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={"composio_response": composio_response},
        )
