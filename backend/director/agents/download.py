import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, TextContent, MsgStatus
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)


class DownloadAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "download"
        self.description = "Get the download URLs of the VideoDB generated streams."
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def run(
        self,
        stream_link: str,
        name: str = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Downloads the video from the given stream link.

        :param stream_link: The URL of the video stream to download.
        :type stream_link: str
        :param name: Optional name for the video stream. If not provided, defaults to None.
        :type name: str, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the download operation.
        :rtype: AgentResponse
        """
        try:
            text_content = TextContent(agent_name=self.agent_name)
            text_content.status_message = "Downloading.."
            self.output_message.content.append(text_content)
            self.output_message.push_update()
            videodb_tool = VideoDBTool()
            download_response = videodb_tool.download(stream_link, name)
            if download_response.get("status") == "done":
                download_url = download_response.get("download_url")
                name = download_response.get("name")
                text_content.text = (
                    f"<a href='{download_url}' target='_blank'>{name}</a>"
                )
                text_content.status = MsgStatus.success
                text_content.status_message = "Here is the download link"
                self.output_message.publish()
            else:
                text_content.status = MsgStatus.error
                text_content.status_message = "Download failed"
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message=f"Downloda failed with {download_response}",
                )
        except Exception as e:
            text_content.status = MsgStatus.error
            text_content.status_message = "Download failed"
            logger.exception(f"error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Download successful.",
            data=download_response,
        )
