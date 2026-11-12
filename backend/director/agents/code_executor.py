from director.agents.base import AgentResponse
from director.agents.sandbox_agent import SandboxAgent

# Prepended to every run so `conn` is ready without boilerplate.
CODE_PRELUDE = """\
import os, json
import videodb

conn = (
    videodb.connect(base_url=os.getenv("VIDEO_DB_BASE_URL", "https://api.videodb.io"))
    if os.getenv("VIDEO_DB_API_KEY")
    else None
)
"""

CODE_EXECUTOR_PARAMETERS = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": """Python code to run. `conn` (a connected VideoDB client), `videodb`, `os` and `json` are already in scope, so don't import or connect again.

- Anything you print (stdout and stderr) is returned to you; print what you need to answer.
- Every call starts in a fresh, empty directory. Variables and files do not carry over between calls.""",
        },
        "progress_message": {
            "type": "string",
            "description": "Short, user-friendly description of what the code does, e.g. 'Listing videos in the collection'.",
        },
    },
    "required": ["code", "progress_message"],
}


class CodeExecutorAgent(SandboxAgent):
    language = "python"

    def __init__(self, session=None, **kwargs):
        self.agent_name = "code_executor"
        self.description = (
            "Runs Python code against VideoDB in a sandbox and returns what it prints. "
            "Use it for anything the other agents don't cover, such as custom queries "
            "over a collection, batch operations or data processing."
        )
        self.parameters = CODE_EXECUTOR_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self, code: str, progress_message: str = "", *args, **kwargs
    ) -> AgentResponse:
        return self.execute(
            code,
            progress_message,
            lambda sandbox, secrets: sandbox.run_code(
                CODE_PRELUDE + code, secrets=secrets
            ),
        )
