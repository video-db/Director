import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session
from director.agents.video_generation import VideoGenerationAgent
from director.agents.video_generation import VIDEO_GENERATION_AGENT_PARAMETERS

logger = logging.getLogger(__name__)

COMPARISON_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "job_type": {
            "type": "string",
            "enum": ["video_generation_comparison"],
            "description": """Type of comparison job to perform
                Available job types:
                    - video_generation_comparison: Run multiple runs of @video_generation agent with different inputs/configurations and compare the outputs
            """,
        },
        "video_generation_comparison": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the video generation run, Mentioned the configuration picked for the run, keep it short ",
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
        self.description = "This agent can be used when user wants to run a single agent multiple times but with different inputs/configurations and compare the outputs"
        self.parameters = COMPARISON_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

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
                video_gen_agent = VideoGenerationAgent(session=self.session)
                results = []
 #
                for params in video_generation_comparison:
                    self.output_message.actions.append(
                        f"{params['description']}"
                    )
                    self.output_message.push_update()

                    result = video_gen_agent.run(**params, stealth_mode=True)
                    print("we got this result", result)
                    # results.append(
                    #     {
                    #         "engine": params["engine"],
                    #         "video_id": result.data["video_id"],
                    #         "video_url": result.data["video_stream_url"],
                    #     }
                    # )

                # return AgentResponse(
                #     status=AgentStatus.SUCCESS,
                #     message="Video generation comparison complete",
                #     data={"results": results},
                # )
            else:
                raise Exception(f"Unsupported comparison type: {job_type}")

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
