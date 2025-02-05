import logging
import json
import os
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session, 
    MsgStatus, 
    TextContent,
    ContextMessage,
    RoleTypes
    
)
from director.llm import get_default_llm
from director.llm.base import LLMResponseStatus

from director.tools.videodb_tool import VideoDBTool
from director.tools.composio_tool import composio_tool, ToolsType

logger = logging.getLogger(__name__)

SALES_ASSISTANT_PARAMETER = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The ID of the sales call video",
        },
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection which the video belongs to"
        },
        "prompt": {
            "type": "string",
            "description": "Additional information/query given by the user to make the appropriate action to take place"
        }
    },
    "required": ["video_id", "collection_id"]
}


SALES_ASSISTANT_PROMPT = """
    Under "transcript", transcript of a sales call video is present.
    Under "user prompt", the user has given additional context or information given
    Generate a sales summary from it and generate answers from the transcript for the following properties

    Following are the properties for which you need to find answers for and the Field type definition or the only possible answers to answer are given below
    
    Each field has a predefined format or set of possible values and can also have **default** property which needs to be used if a field is missing in transcript and user prompt:  

    #### **Fields & Expected Answers**  
    Field: dealname
    description: (The company or individuals name with whom we are making a deal with)
    type: text (which says the name of person we are dealing with or the company)

    Field: dealstage
    Possible Answers: appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, closedwon, closedlost
    default: appointmentscheduled

    Field: budget
    type: Multi line text (Around 150 words description)
    description: 
        The multi line text answer for this field must consist of a detailed analysis of the budget situation of the company. 
        If numbers are mentioned, do include those details aswell.
        If the deal is overpriced, underpriced or considered fair, should also be added if mentioned


    Field: authority
    type: Multi line text (Around 150 words description)
    description: 
        The multi line text answer for this field must consist of a detailed analysis of the authority the client possesses for the conclusion of the deal. 
        If decision making powers are mentioned, do include those details.
        If the client mention that they are the final signing authority, or any other details signifying their level of power in the deal. mention them
        

    Field: need
    type: Multi line text (Around 150 words description)
    description: 
        The multi line text answer for this field must consist of a detailed analysis of how much the client wants the product. 
        Need can be found from the level or urgency, the depth or importance of problem they want to get solved or the amount of hurry they have
        

    Field: timeline
    type: Multi line text (Around 150 words description)
    description: 
        The multi line text answer for this field must consist of a detailed analysis of how the timeline of the project looks like
        Mention when they need the product, when they want to test the product etc. Important details about the timelines must be added here.

"""


class SalesAssistantAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "sales_assistant"
        self.description = "This agent will transcribe sales calls, automatically create deal summaries & update CRM software like Salesforce & Hubspot"
        self.parameters = SALES_ASSISTANT_PARAMETER
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)


    def _generate_prompt(self, transcript:str, prompt:str):
        final_prompt = SALES_ASSISTANT_PROMPT

        final_prompt += f"""
            "transcript":
            {transcript}

            "user prompt":
            {prompt}
        """

        return final_prompt
    
    def run(self, 
            video_id:str,
            collection_id:str,
            prompt="",
            *args, 
            **kwargs
            ) -> AgentResponse:
        """
        Create deal summaries and update the users CRM software

        :param str video_id: The sales call video ID
        :param str collection_id: The videos collection ID
        :param str prompt: Additional context or query given by the user for the task
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

            if not HUBSPOT_ACCESS_TOKEN:
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Hubspot token not present"
                )

            text_content = TextContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Making magic happen with VideoDB Director...",
            )

            self.output_message.content.append(text_content)
            self.output_message.push_update()

            videodb_tool = VideoDBTool(collection_id=collection_id)

            self.output_message.actions.append("Extracting the transcript")
            self.output_message.push_update()

            try:
                transcript_text = videodb_tool.get_transcript(video_id)
            except Exception:
                logger.error("Transcript not found. Indexing spoken words..")
                self.output_message.actions.append("Indexing spoken words..")
                self.output_message.push_update()
                videodb_tool.index_spoken_words(video_id)
                transcript_text = videodb_tool.get_transcript(video_id)

            self.output_message.actions.append("Processing the transcript")
            self.output_message.push_update()

            sales_assist_llm_prompt = self._generate_prompt(transcript=transcript_text, prompt=prompt)
            sales_assist_llm_message = ContextMessage(
                content=sales_assist_llm_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions([sales_assist_llm_message.to_llm_msg()])
            
            if not llm_response.status:
                logger.error(f"LLM failed with {llm_response}")
                text_content.status = MsgStatus.error
                text_content.status_message = "Failed to generate the response."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Sales assistant failed due to LLM error.",
                )
            
            composio_prompt = f"""
                Create a new deal in HubSpot with the following details:

                ---
                {llm_response.content}
                ---

                Use the HUBSPOT_CREATE_CRM_OBJECT_WITH_PROPERTIES action to accomplish this.
                """
            
            self.output_message.actions.append("Adding it into the Hubspot CRM")
            self.output_message.push_update()
            
            composio_response = composio_tool(
                task=composio_prompt,
                auth_data={
                    "name": "HUBSPOT",
                    "token": HUBSPOT_ACCESS_TOKEN
                },
                tools_type=ToolsType.actions
            )

            llm_prompt = (
                f"User has asked to run a task: {composio_prompt} in Composio. \n"
                "Dont mention the action name directly as is"
                "Comment on the fact whether the composio call was sucessful or not"
                "Make this message short and crisp"
                f"{json.dumps(composio_response)}"
                "If there are any errors or if it was not successful, do tell about that as well"
            )
            final_message = ContextMessage(content=llm_prompt, role=RoleTypes.user)
            llm_response = self.llm.chat_completions([final_message.to_llm_msg()])
            if llm_response.status == LLMResponseStatus.ERROR:
                raise Exception(f"LLM Failed with error {llm_response.content}")

            text_content.text = llm_response.content
            text_content.status = MsgStatus.success
            text_content.status_message = "Here is the response from Composio"
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            text_content.status = MsgStatus.error
            text_content.status_message = "Error in sales assistant"
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={},
        )
