import logging
import concurrent.futures
import queue

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, VideosContent, VideoData, MsgStatus
from director.agents.video_generation import VideoGenerationAgent
from director.agents.video_generation import VIDEO_GENERATION_AGENT_PARAMETERS

logger = logging.getLogger(__name__)

COMPARISON_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "job_type": {
            "type": "string",
            "enum": ["video_generation_comparison"],
            "description": "Creates videos using MULTIPLE video generation models/engines. This agent should be used in two scenarios: 1) When request contains model names connected by words like 'and', '&', 'with', ',', 'versus', 'vs' (e.g. 'using Stability and Kling'), 2) When request mentions comparing/testing multiple models even if mentioned later in the prompt (e.g. 'Generate X. Compare results from Y, Z'). If the request suggests using more than one model in any way, use this agent rather than calling video_generation agent multiple times.",
        },
        "video_generation_comparison": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the video generation run, Mention the configuration picked for the run. Keep the engine name and parameter config in a separate line. Keep it short. Here's an example: 'Tokyo Sunset - Luma - Prompt: 'An aerial shot of a quiet sunset at Tokyo', Duration: 5s, Luma Dream Machine",
                    },
                    **VIDEO_GENERATION_AGENT_PARAMETERS["properties"],
                },
                "required": [
                    "description",
                    *VIDEO_GENERATION_AGENT_PARAMETERS["required"],
                ],
                "description": "Parameters to use for each video generation run, each object in this is the parameters that would be required for each @video_generation run",
            },
            "description": "List of parameters to use for each video generation run, each object in this is the parameters that would be required for each @video_generation run",
        },
    },
    "required": ["job_type", "video_generation_comparison"],
}


class ComparisonAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "comparison"
        self.description = """Primary agent for video generation from prompts. Handles all video creation requests including single and multi-model generation. If multiple models or variations are mentioned, automatically parallelizes the work. For single model requests, delegates to specialized video generation subsystem. Keywords: generate video, create video, make video, text to video. """

        self.parameters = COMPARISON_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def _run_video_generation(self, index, params):
        """Helper method to run video generation with given params"""
        video_gen_agent = VideoGenerationAgent(session=self.session)
        return (index, video_gen_agent.run(**params, stealth_mode=True))

    def done_callback(self, fut):
        result = fut.result()
        self.notification_queue.put(result)

    def _update_videos_content(self, videos_content, index, result):
        if result.status == AgentStatus.SUCCESS:
            videos_content.videos[index] = result.data["video_content"].video
        elif result.status == AgentStatus.ERROR:
            videos_content.videos[index] = VideoData(
                name=f"[Error] {videos_content.videos[index].name}",
                stream_url="",
                id=None,
                collection_id=None,
            )
        self.output_message.push_update()

    def run(
        self, job_type: str, video_generation_comparison: list, *args, **kwargs
    ) -> AgentResponse:
        """
        Compare outputs from multiple runs of video generation

        :param str job_type: Type of comparison to perform
        :param list video_generation_comparison: Parameters for video gen runs
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Response containing comparison results
        :rtype: AgentResponse
        """
        try:
            if job_type == "video_generation_comparison":
                videos_content = VideosContent(
                    agent_name=self.agent_name,
                    status=MsgStatus.progress,
                    status_message="Generating videos (Usually takes 3-7 mins)",
                    videos=[],
                )
                self.notification_queue = queue.Queue()

                for params in video_generation_comparison:
                    video_data = VideoData(
                        name=params["text_to_video"]["name"],
                        stream_url="",
                    )
                    videos_content.videos.append(video_data)

                self.output_message.content.append(videos_content)
                self.output_message.push_update()

                # Use ThreadPoolExecutor to run video generations in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit all tasks and get future objects
                    futures = []
                    for index, params in enumerate(video_generation_comparison):
                        future = executor.submit(
                            self._run_video_generation, index, params
                        )
                        future.add_done_callback(self.done_callback)
                        futures.append(future)

                    # Process completed tasks as they finish
                    completed_count = 0
                    total = len(futures)

                    while completed_count < total:
                        res = self.notification_queue.get()
                        self._update_videos_content(videos_content, res[0], res[1])
                        completed_count += 1

                    for future in concurrent.futures.as_completed(futures):
                        try:
                            videos_content.status = MsgStatus.success
                            videos_content.status_message = (
                                "Here are your generated videos"
                            )
                            self.output_message.push_update()
                        except Exception as e:
                            logger.exception(f"Error processing task: {e}")

                return AgentResponse(
                    status=AgentStatus.SUCCESS,
                    message="Video generation comparison complete",
                    data={"videos": videos_content},
                )
            else:
                raise Exception(f"Unsupported comparison type: {job_type}")

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
