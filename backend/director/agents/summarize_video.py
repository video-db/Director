import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import ContextMessage, RoleTypes, TextContent, MsgStatus
from director.llm import get_default_llm
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)


class SummarizeVideoAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "summarize_video"
        self.description = "This is an agent to summarize the given video of VideoDB, if the user wants a certain kind of summary the prompt is required."
        self.llm = get_default_llm()
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        video_id: str,
        prompt: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generate summary of the given video.

        :param str collection_id: The collection_id where given video_id is available.
        :param str video_id: The id of the video for which the video player is required.
        :param str prompt: The prompt to guide the summary generation.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse

        """
        try:
            self.output_message.actions.append("Started summary generation..")
            output_text_content = TextContent(
                agent_name=self.agent_name, status_message="Generating the summary.."
            )
            self.output_message.content.append(output_text_content)
            self.output_message.push_update()
            videodb_tool = VideoDBTool(collection_id=collection_id)
            try:
                transcript_text = videodb_tool.get_transcript(video_id)
            except Exception:
                logger.error("Failed to get transcript, indexing")
                self.output_message.actions.append("Indexing the video..")
                self.output_message.push_update()
                videodb_tool.index_spoken_words(video_id)
                transcript_text = videodb_tool.get_transcript(video_id)
            summary_llm_prompt = f"{transcript_text} {prompt}"
            summary_llm_message = ContextMessage(
                content=summary_llm_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions([summary_llm_message.to_llm_msg()])
            if not llm_response.status:
                logger.error(f"LLM failed with {llm_response}")
                output_text_content.status = MsgStatus.failed
                output_text_content.status_message = "Failed to generat the summary."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Summary failed due to LLM error.",
                )
            summary = llm_response.content
            output_text_content.text = summary
            output_text_content.status = MsgStatus.success
            output_text_content.status_message = "Here is your summary"
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent.")
            output_text_content.status = MsgStatus.error
            output_text_content.status_message = "Error in generating summary."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Summary generated and displayed to user.",
            data={"summary": summary},
        )
