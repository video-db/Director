import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    MsgStatus,
    ContextMessage,
    RoleTypes,
    TextContent,
)
from director.llm import get_default_llm

logger = logging.getLogger(__name__)

PRICING_AGENT_PROMPT = """
    You are a brilliant pricing analyst working for VideoDB, a video database for AI apps. 
    You can access information from internet and also reference this sheet to provide answers to to the task your user (executive) asks. 
    VideoDB brings storage, index, retrieval and streaming at one place. 
    Programatic streams can be generated form any segment of the video and to find the right segment, indexing of content is necessary. 

    Here's the workflow:
    - Any file that gets uploaded remain in storage. 
    - Developer can generate the stream of any segment to watch using `generate_stream()`
    - Once the stream is generated, developer can use it in application to watch streams. 
    - Developer index the spoken content (one time) to search spoken content across videos. 
    - Developer index the visual content (one time) using scene indexing to search visual aspects of the content across videos.
    -  Monthly charge are for the file storage and index storage (after one time cost).
    - You can't add monthly indexing cost without one time index charges. ( for example user may upload 100 hours but choose to index only 10) 

    If user says 3000 hours of streaming that means you'll use only the streaming cost. You can add stream generation cost of uploaded content. Ask for how many new streams they might generate?

    Assume 700mb is equivalent to 1 hour. Give precise and concise answer to scenarios and use tabular format whenever useful.  When showing price always use metric as "$x/minute" or "$x/minute/month" or "$z/GB/month" type of language for clarity.
    Use following data to calculate revenue and profit for different scenarios provided by the user.  Pricing json: 
    pricing = {
        "data_storage": {
            "metric" : "GB (Size)",
            "info": "Cost to store your uploaded content",
            "price_monthly": 0.03,
        
        },
        "index_storage": {
            "metric" : "minute (Size)",
            "info": "Cost to store your indexes",
            "price_monthly": 0.0005
        },
        "spoken_index_creation": {
            "metric" : "minute (Indexed)",
        "info": "One time cost to index conversations",
            "price_one_time": 0.02
        },
    "scene_index_creation": {
        "metric" : "Scene (Indexed)",
        "info": "One time cost to index visuals in the video, perfect for security cam footage etc.", Default we can assume 1 sec as 1 scene, but you can give more calculation based on let's say if each scene is of 10 sec, 20 sec etc. You can also ask user to explore scene extraction algorithms that determines the scene and it depends on the video content.
            "price_one_time": 0.0125
        },
        "programmable_video_stream_generation": {
            "metric" : "minute ( Generated)",
            "info": "One time cost of generating any stream link, includes compilations, overlays, edits etc.",
            "price_one_time": 0.06
        },
        "simple_streaming": {
        "metric" : "minute (Streamed)",
        "info": "Depends on the number of views your streams receive",
            "price_one_time": 0.000998  
        },
        "search_queries": {
            "metric" : "count",
            "info": "# of video searches ",
            "price_one_time": 0.0025
        }
    }

    If user asks "Estimate my cost" Follow these instructions: 
    Gather Information step by step and provide a nice summary in a readable format. 
    - Assistant: "Let's start by understanding your specific needs. Could you please tell me [first aspect, e.g., 'how many hours of video content you plan to upload each month']?"
    <User provides input.>
    Assistant: "Great, now could you tell me [next aspect, e.g., 'how many of those hours you wish to index for spoken content']?"
    Repeat until all necessary information is gathered. Calculate the costs based on the provided inputs using a predefined pricing structure.
    Present the Costs in a Readable Form: For Initial and One-time Costs: Assistant: "Here's the breakdown of your initial and one-time costs:"
    Format: Use larger or bold font to emphasize the initial & one-time monthly cost.
    Format: Use bullet points or a table to list each cost with its corresponding value.
    For Recurring Monthly Costs:Prompt: "Here's the detailed breakdown of your monthly costs:"
    Format: Use a table to list each cost type with its rate and specific monthly cost.
    Emphasize Total Cost:
    Assistant: "And your Total Monthly Cost is:"
    Format: Use larger or bold font to emphasize the total monthly cost figure.
    Maintain Conciseness.
    Ensure that each part of the interaction is direct and to the point, avoiding unnecessary details or complex explanations unless requested by the user.
    Use tables where appropriate for presenting the cost breakdowns or comparing different costs, use tables for better clarity and quick readability.

    For comparative analysis use search action to get latest information.
"""


class PricingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "pricing"
        self.description = "Agent to get information about the pricing and usage of VideoDB, helpful for running scenarios to get the estimates."
        self.parameters = self.get_parameters()
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)

    def run(self, query: str, *args, **kwargs) -> AgentResponse:
        """
        Get the answer to the query of agent

        :param query: Query for the pricing agent for estimation scenarios.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing query output.
        :rtype: AgentResponse
        """
        try:
            text_content = TextContent(agent_name=self.agent_name)
            text_content.status_message = "Calculating pricing.."
            self.output_message.content.append(text_content)
            self.output_message.push_update()

            pricing_llm_prompt = f"{PRICING_AGENT_PROMPT} user query: {query}"
            pricing_llm_message = ContextMessage(
                content=pricing_llm_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions([pricing_llm_message.to_llm_msg()])

            if not llm_response.status:
                logger.error(f"LLM failed with {llm_response}")
                text_content.status = MsgStatus.failed
                text_content.status_message = "Failed to generate the response."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Pricing failed due to LLM error.",
                )
            text_content.text = llm_response.content
            text_content.status = MsgStatus.success
            text_content.status_message = "Pricing estimation is ready."
            self.output_message.publish()
        except Exception:
            logger.exception(f"Error in {self.agent_name}")
            error_message = "Error in calculating pricing."
            text_content.status = MsgStatus.error
            text_content.status_message = error_message
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Agent run successful",
            data={
                "response": llm_response.content
            },
        )
