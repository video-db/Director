import logging
import os

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    TextContent,
    MsgStatus,
    ContextMessage,
    RoleTypes,
)
from director.tools.slack import send_message_to_channel
from director.llm import get_default_llm
from director.llm.base import LLMResponseStatus

logger = logging.getLogger(__name__)

# Slack App Setup:
# 1. Go to https://api.slack.com/apps and create a new app
# 2. Add the 'chat:write' OAuth scope under 'Bot Token Scopes'
# 3. Install the APP in your slack workspace
# 4. Copy the 'Bot User OAuth Token' and set it as an environment variable SLACK_BOT_TOKEN
# 5. Invite the bot to the channel where you want to send messages
# 6. Set the channel name where bot can send the message to SLACK_CHANNEL_NAME


class SlackAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "slack"
        self.description = "Messages to a slack channel"
        self.parameters = self.get_parameters()
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)

    def run(self, message: str, *args, **kwargs) -> AgentResponse:
        """
        Send a message to a slack channel.
        :param str message: The message to send to the slack channel_name.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the slack message operation.
        :rtype: AgentResponse
        """
        channel_name = os.getenv("SLACK_CHANNEL_NAME")
        if not channel_name:
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="Please set the SLACK_CHANNEL_NAME in the .env",
            )
        text_content = TextContent(
            agent_name=self.agent_name,
            status=MsgStatus.progress,
            status_message="Sending message to slack..",
        )
        self.output_message.content.append(text_content)
        self.output_message.push_update()
        try:
            # TOOD: Need improvemenents in below prompt
            slack_llm_prompt = (
                "Format the following message that slack can render nicely.\n"
                "Give the output which can be directly passed to slack (no blockquotes until required because of code etc.)\n"
                "Also, don't include you can copy this message etc.\n"
                f"message: {message}"
            )
            slack_message = ContextMessage(
                content=slack_llm_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions([slack_message.to_llm_msg()])
            if llm_response.status == LLMResponseStatus.ERROR:
                raise Exception(f"LLM Failed with error {llm_response.content}")
            formatted_message = llm_response.content
            self.output_message.actions.append("Sending message to slack..")
            response = send_message_to_channel(formatted_message, channel_name)
            text_content.text = formatted_message
            text_content.status = MsgStatus.success
            text_content.status_message = (
                f"Here is the slack message sent to {channel_name}"
            )
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Message sent to slack channel: {channel_name}",
                data={
                    "channel_name": channel_name,
                    "message": formatted_message,
                    "ts": response["ts"],
                },
            )
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            text_content.status = MsgStatus.error
            text_content.status_message = f"Error sending message to slack: {str(e)}"
            self.output_message.publish()
            error_message = f"Agent failed with error: {str(e)}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
