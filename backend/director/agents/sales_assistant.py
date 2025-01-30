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
    default: Deal with John Doe

    Field: dealstage
    Possible Answers: appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, closedwon, closedlost
    default: appointmentscheduled

    Field: budget
    type: text (which signifies a budget range for eg: $1500 - $2000, $10000, etc)
    default: undisclosed

    Field: authority
    Possible Answers: Decision Maker, Influencer, Champion, No Authority
    default: Influencar

    Field: need
    Possible Answers: Critical, Important, Nice to Have, Not a Fit
    default: Important

    Field: timeline
    Possible Answers: This Month, This Quarter, Next Quarter, Next Year,Uncertain
    default: This Quarter

If any field is missing in the transcript, return **'Unknown'** or any suitable value for it if the "default" is not present.  
 
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
                status_message="Making magic happen with VideoDB Director..",
            )

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
                "Format the following reponse into text.\n"
                "Give the output which can be directly send to use \n"
                "Don't add any extra text \n"
                f"{json.dumps(composio_response)}"
                "If there are any errors or if it was not successful, do tell about that as well"
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
            text_content.status_message = "Error in sales assistant"
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={},
        )
