import json
import logging

from abc import ABC, abstractmethod
from pydantic import BaseModel

from openai_function_calling import FunctionInferrer

from director.core.permissions import CallInfo
from director.core.session import Session, OutputMessage

logger = logging.getLogger(__name__)


class AgentStatus:
    SUCCESS = "success"
    ERROR = "error"


class AgentResponse(BaseModel):
    """Data model for respones from agents."""

    status: str = AgentStatus.SUCCESS
    message: str = ""
    data: dict = {}


class BaseAgent(ABC):
    """Interface for all agents. All agents should inherit from this class."""

    # True when the agent never changes anything; it then runs in every mode.
    read_only: bool = False
    # How this call was approved, shown on its output (set by the engine).
    approved_by: str = ""

    def __init__(self, session: Session, **kwargs):
        self.session: Session = session
        self.output_message: OutputMessage = self.session.output_message

    def get_parameters(self):
        """Return the automatically inferred parameters for the function using the dcstring of the function."""
        function_inferrer = FunctionInferrer.infer_from_function_reference(self.run)
        function_json = function_inferrer.to_json_schema()
        parameters = function_json.get("parameters")
        if not parameters:
            raise Exception(
                "Failed to infere parameters, please define JSON instead of using this automated util."
            )

        parameters["properties"].pop("args", None)
        parameters["properties"].pop("kwargs", None)

        if "required" in parameters:
            parameters["required"] = [
                param
                for param in parameters["required"]
                if param not in ["args", "kwargs"]
            ]

        return parameters

    def inspect(self, **arguments) -> CallInfo:
        """Describe a call before it runs, for the permission check. Executors override this."""
        return CallInfo(
            preview=json.dumps(arguments, indent=2, default=str),
            language="json",
            read_only=self.read_only,
            key=self.agent_name,
        )

    def to_llm_format(self):
        """Convert the agent to LLM tool format."""
        return {
            "name": self.agent_name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @property
    def name(self):
        return self.agent_name

    @property
    def agent_description(self):
        return self.description

    def safe_call(self, *args, **kwargs):
        try:
            return self.run(*args, **kwargs)

        except Exception as e:
            logger.exception(f"error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

    @abstractmethod
    def run(*args, **kwargs) -> AgentResponse:
        pass
