from director.agents.base import AgentResponse
from director.agents.sandbox_agent import SandboxAgent

BASH_EXECUTOR_PARAMETERS = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": """Bash command to run. Pipes, redirects and multi-line scripts work.

- stdout, stderr and the exit code are returned to you.
- Every call starts in a fresh, empty directory; files do not carry over between calls.
- `python` has the videodb package installed, and VIDEO_DB_API_KEY is set when configured.""",
        },
        "progress_message": {
            "type": "string",
            "description": "Short, user-friendly description of what the command does, e.g. 'Downloading the clip'.",
        },
        "timeout": {
            "type": "integer",
            "description": "Optional timeout in seconds. Defaults to the sandbox limit.",
        },
    },
    "required": ["command", "progress_message"],
}


class BashExecutorAgent(SandboxAgent):
    language = "bash"

    def __init__(self, session=None, **kwargs):
        self.agent_name = "bash_executor"
        self.description = (
            "Runs a bash command in a sandbox and returns stdout, stderr and the exit code. "
            "Use it to read skills, run a skill's helper scripts, or use tools like ffmpeg and curl."
        )
        self.parameters = BASH_EXECUTOR_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        command: str,
        progress_message: str = "",
        timeout: int = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        return self.execute(
            command,
            progress_message,
            lambda sandbox, secrets: sandbox.run_bash(
                command, secrets=secrets, timeout=timeout
            ),
        )
