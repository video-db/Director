import logging
from typing import List

from director.agents.base import BaseAgent, AgentStatus, AgentResponse
from director.core.context import ContextBuilder, ContextPolicy
from director.core.prompts import SUMMARIZATION_PROMPT
from director.core.session import (
    Session,
    InputMessage,
    ContextMessage,
    RoleTypes,
    TextContent,
    MsgStatus,
)
from director.llm.base import BaseLLM, LLMResponse


logger = logging.getLogger(__name__)


class ReasoningEngine:
    """The Reasoning Engine is the core class that directly interfaces with the user. It interprets natural language input in any conversation and orchestrates agents to fulfill the user's requests.

    Each turn it calls the LLM with the registered agents as tools, runs the requested agents, feeds their responses back, and repeats until the LLM answers without tools or ``max_iterations`` is reached. If any agent ran, a final summarization pass ("Final Cut") writes the reply."""

    def __init__(
        self,
        session: Session,
        llm: BaseLLM,
        agents: List[BaseAgent],
        context: ContextBuilder = None,
        policy: ContextPolicy = None,
        max_iterations: int = 10,
    ):
        """Initialize the ReasoningEngine.

        :param session: The session instance.
        :param llm: The LLM used for reasoning and summarization.
        :param agents: The agents offered to the LLM as tools.
        :param context: Builds the reasoning context for a turn.
        :param policy: Trims the context sent to the LLM.
        :param max_iterations: Max LLM calls before the turn is closed.
        """
        self.session = session
        self.llm = llm
        self.agents = {agent.agent_name: agent for agent in agents}
        self.context = context or ContextBuilder()
        self.policy = policy or ContextPolicy()
        self.max_iterations = max_iterations
        self.output_message = session.output_message
        self.failed_agents = []

    def run(self, input_message: InputMessage):
        """Run the reasoning engine for one user message.

        :param input_message: The input message to the reasoning engine.
        """
        ctx = self.context.build(self.session, input_message)
        self.output_message.actions.append("Reasoning the message..")
        self.output_message.push_update()
        tools = [agent.to_llm_format() for agent in self.agents.values()]
        used_tools = False

        for _ in range(self.max_iterations):
            response: LLMResponse = self.llm.chat_completions(
                messages=self.policy.apply(ctx), tools=tools
            )
            logger.info(f"LLM Response: {response}")

            if not response.status:
                self._fail(response)
                break

            if response.tool_calls:
                used_tools = True
                ctx.append(
                    ContextMessage(
                        content=response.content,
                        tool_calls=response.tool_calls,
                        role=RoleTypes.assistant,
                    )
                )
                for tool_call in response.tool_calls:
                    ctx.append(self._run_tool(tool_call))
                continue

            ctx.append(
                ContextMessage(content=response.content, role=RoleTypes.assistant)
            )
            self._finish(response.content, used_tools)
            break
        else:
            # Hit max_iterations while the LLM was still calling agents.
            self._finish(None, used_tools=True)

        self.session.save_context_messages()

    def _run_tool(self, tool_call: dict) -> ContextMessage:
        """Run the agent requested by a tool call and return its tool message."""
        agent_name = tool_call["tool"]["name"]
        arguments = tool_call["tool"]["arguments"]
        logger.info(f"Running {agent_name} agent with {arguments}")

        agent = self.agents.get(agent_name)
        if agent:
            self.output_message.actions.append(f"Running @{agent_name} agent")
            self.output_message.agents.append(agent_name)
            self.output_message.push_update()
            agent_response = agent.safe_call(**arguments)
        else:
            agent_response = AgentResponse(
                status=AgentStatus.ERROR, message=f"Unknown agent: {agent_name}"
            )

        if agent_response.status == AgentStatus.ERROR:
            self.failed_agents.append(agent_name)
        return ContextMessage(
            content=agent_response.__str__(),
            tool_call_id=tool_call["id"],
            role=RoleTypes.tool,
        )

    def _finish(self, text: str, used_tools: bool):
        """Write the reply: the direct answer if no agent ran, otherwise a summary of the turn."""
        summary = TextContent(agent_name="assistant")
        summary.status_message = "Consolidating outcomes..."
        self.output_message.content.append(summary)
        self.output_message.push_update()

        if not used_tools:
            summary.text = text
            summary.status_message = "Here is the response"
            summary.status = MsgStatus.success
        else:
            run_context = self._current_run_context() + [
                ContextMessage(content=SUMMARIZATION_PROMPT, role=RoleTypes.system)
            ]
            summary_response = self.llm.chat_completions(
                messages=[message.to_llm_msg() for message in run_context]
            )
            summary.text = summary_response.content
            summary.status_message = "Final Cut"
            summary.status = (
                MsgStatus.error if self.failed_agents else MsgStatus.success
            )

        self.output_message.status = MsgStatus.success
        self.output_message.publish()

    def _fail(self, response: LLMResponse):
        self.output_message.content.append(
            TextContent(
                text=response.content,
                status=MsgStatus.error,
                status_message="Error in reasoning",
                agent_name="assistant",
            )
        )
        self.output_message.actions.append("Failed to reason the message")
        self.output_message.status = MsgStatus.error
        self.output_message.publish()

    def _current_run_context(self) -> List[ContextMessage]:
        """Context from the latest user message onwards."""
        ctx = self.session.reasoning_context
        for i in range(len(ctx) - 1, -1, -1):
            if ctx[i].role == RoleTypes.user:
                return ctx[i:]
        return []
