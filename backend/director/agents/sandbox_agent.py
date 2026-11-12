import logging
import os

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.sandbox import ExecResult
from director.core.session import MsgStatus, TextContent

logger = logging.getLogger(__name__)

# Env passed into every sandbox call so code can reach VideoDB.
SANDBOX_SECRET_ENV = ("VIDEO_DB_API_KEY", "VIDEO_DB_BASE_URL")

MAX_OUTPUT_CHARS = 8000


class SandboxAgent(BaseAgent):
    """Shared flow for agents that run something in `session.sandbox`: show it, run it, return its output to the LLM."""

    language = ""

    def execute(self, source: str, progress_message: str, run) -> AgentResponse:
        """Show `source` to the user, call `run(sandbox, secrets)` and turn its ExecResult into an AgentResponse."""
        sandbox = getattr(self.session, "sandbox", None)
        if sandbox is None:
            return AgentResponse(
                status=AgentStatus.ERROR, message="No sandbox is configured."
            )

        title = progress_message or "Running code"
        self.output_message.actions.append(title)
        self.output_message.content.append(
            TextContent(
                text=f"```{self.language}\n{source}\n```",
                status=MsgStatus.success,
                status_message=title,
                agent_name=self.agent_name,
            )
        )
        self.output_message.push_update()

        secrets = {key: os.environ[key] for key in SANDBOX_SECRET_ENV if os.getenv(key)}
        result: ExecResult = run(sandbox, secrets)
        logger.info(f"{self.agent_name} exited with {result.exit_code}")

        return AgentResponse(
            status=AgentStatus.SUCCESS if result.ok else AgentStatus.ERROR,
            message="Ran successfully"
            if result.ok
            else f"Exited with code {result.exit_code}",
            data={
                "stdout": truncate(result.stdout),
                "stderr": truncate(result.stderr),
                "exit_code": result.exit_code,
            },
        )


def truncate(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Keep the head and tail of long output so it doesn't flood the LLM context."""
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"{text[: max_chars // 2]}\n\n... [{omitted} chars truncated] ...\n\n{text[-max_chars // 2 :]}"
