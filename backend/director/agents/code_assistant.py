import logging
import json
import requests
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import ContextMessage, RoleTypes, TextContent, MsgStatus
from director.llm import get_default_llm

logger = logging.getLogger(__name__)

CODE_ASSISTANT_AGENT_PROMPT = """
You are a technical assistant for customers of VideoDB, a specialized video management library.
Your role is to assist users by answering their queries using the VideoDB DB CONTEXT provided below.

Your response should:
    - Be accurate and context-aware, using only the information from the VideoDB context.
    - Include relevant Python code snippets when applicable.
    - Enclose all code in proper Markdown formatting using triple backticks and specify the language, e.g.,

```python
code here


Instructions:
    - Read the user query carefully.
    - Use the VideoDB context to generate your response.
    - If code is required, provide clean, working Python examples.

Return a JSON with two keys, Don't Add ``` json before or after the text, just send the object as string
- heading : a 2-3 words heading that describes the response well
- response: actual response from you
"""

# Define the fixed file path for the additional context.
VIDEODB_LLMS_FULL_TXT_URL = (
    "https://videodb.io/llms-full.txt"
)


class CodeAssistantAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "code_assistant"
        self.description = (
            "This agent generates VideoDB-related code from a natural language requirement. "
            "It constructs a prompt for the LLM, processes the response, extracts the code snippet, "
            "and prints it for the user. The additional context for the LLM prompt is downloaded from a URL."
        )
        self.llm = get_default_llm()
        self.parameters = {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Natural language requirement for generating VideoDB code.",
                }
            },
            "required": ["prompt"],
        }
        super().__init__(session=session, **kwargs)

    def run(self, prompt: str) -> AgentResponse:
        try:
            self.output_message.actions.append(
                f"Generating VideoDB code based on user requirement: {prompt}"
            )
            # Download additional context from the predefined URL.
            response = requests.get(VIDEODB_LLMS_FULL_TXT_URL)
            if response.status_code == 200:
                context_content = response.text
            else:
                error_msg = f"Failed to download context data: {response.status_code}"
                logger.error(error_msg)
                return AgentResponse(status=AgentStatus.ERROR, message=error_msg)

            # Construct the full prompt by combining the loaded context and the user requirement.
            full_prompt = f"""
                  {CODE_ASSISTANT_AGENT_PROMPT}
                  USER REQUIREMENT: {prompt} \n \n
                  VIDEODB CONTEXT : {context_content}\n \n"
                """
            message = ContextMessage(content=full_prompt, role=RoleTypes.user)

            # Get response from the LLM.
            llm_response = self.llm.chat_completions([message.to_llm_msg()])
            if not llm_response.status:
                error_msg = f"LLM failed to generate a response: {llm_response}"
                logger.error(error_msg)
                return AgentResponse(status=AgentStatus.ERROR, message=error_msg)
            llm_response = json.loads(llm_response.content)
            heading = llm_response.get("heading", "Response")
            response = llm_response.get("response", "")

            # Create an output message with the extracted code.
            output_content = TextContent(
                agent_name=self.agent_name, status_message=heading
            )
            output_content.text = response
            output_content.status = MsgStatus.success
            self.output_message.content.append(output_content)
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Response generated successfully.",
                data={"response": response},
            )
        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
