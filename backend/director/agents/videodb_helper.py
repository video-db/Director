import logging
import re
import json
import datetime
import uuid
import boto3
import os
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import ContextMessage, RoleTypes, TextContent, MsgStatus
from director.llm import get_default_llm

logger = logging.getLogger(__name__)

# Define the fixed file path for the additional context.
CONTEXT_FILE_PATH = "director/prompts/videodb-context.txt"

# Define your S3 bucket name
bucket_name = os.environ.get("S3_BUCKET_NAME")
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION")


class VideoDBHelperAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "videodb_helper"
        self.description = (
            "This agent generates VideoDB-related code from a natural language requirement. "
            "It constructs a prompt for the LLM, processes the response, extracts the code snippet, "
            "and prints it for the user. The additional context for the LLM prompt is loaded "
            "from a predefined local file."
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

    def dump_to_s3(self, log_data: dict):
        """
        Dumps the log data as a JSON file to S3. The S3 key is generated using a timestamp
        and a UUID for uniqueness.
        """
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region,
            )

            unique_id = str(uuid.uuid4())
            s3_key = f"hosted_dev/{unique_id}.json"
            json_body = json.dumps(log_data)
            s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=json_body)
            logger.info(f"Successfully dumped log data to s3://{bucket_name}/{s3_key}")
        except Exception as s3_exception:
            logger.exception(f"Failed to dump log data to S3: {s3_exception}")

    def run(self, prompt: str) -> AgentResponse:
        try:
            self.output_message.actions.append(
                "Generating VideoDB code based on user requirement..."
            )
            # Load additional context from the predefined file path.
            with open(CONTEXT_FILE_PATH, "r") as file:
                context_content = file.read()

            # Construct the full prompt by combining the loaded context and the user requirement.
            full_prompt = (
                f"{context_content}\nUser Requirement: {prompt}\n"
                "Please generate the corresponding Python code for VideoDB operations, "
                "including necessary imports and functionality."
            )
            message = ContextMessage(content=full_prompt, role=RoleTypes.user)
            # Get response from the LLM.
            llm_response = self.llm.chat_completions([message.to_llm_msg()])
            if not llm_response.status:
                error_msg = f"LLM failed to generate a response: {llm_response}"
                logger.error(error_msg)
                return AgentResponse(status=AgentStatus.ERROR, message=error_msg)

            generated_text = llm_response.content

            # Extract code blocks from the LLM response using regex (detects code in triple backticks).
            code_snippets = re.findall(
                r"```(?:python)?\n(.*?)```", generated_text, re.DOTALL
            )
            if code_snippets:
                code_output = "\n\n".join(code_snippets)
            else:
                code_output = generated_text  # Fallback if no code blocks are found.

            code_output = f"""```python\n{code_output}\n```"""

            # Create an output message with the extracted code.
            output_content = TextContent(
                agent_name=self.agent_name, status_message="Generated code:"
            )
            output_content.text = code_output
            output_content.status = MsgStatus.success
            self.output_message.content.append(output_content)
            self.output_message.publish()

            # Prepare log data for S3 dump.
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "input": prompt,
                "output": code_output,
                "context_file_path": CONTEXT_FILE_PATH,
                "llm": self.llm.chat_model,
                "session_id": self.session.session_id,
                "conv_id": self.session.conv_id,
            }
            # Dump the log data to the S3 bucket.
            self.dump_to_s3(log_data)

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Code generated successfully.",
                data={"code": code_output},
            )
        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
