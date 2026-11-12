import logging
from typing import List

from director.agents.base import BaseAgent, AgentStatus, AgentResponse
from director.core.context import ContextBuilder, ContextPolicy
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

MAX_ITERATIONS_REPLY = (
    "I stopped before finishing because this request needed more steps than "
    "I'm allowed in one turn. Tell me to continue and I'll pick up from here."
)


class ReasoningEngine:
    """The Reasoning Engine is the core class that directly interfaces with the user. It interprets natural language input in any conversation and orchestrates agents to fulfill the user's requests.

    Each turn it calls the LLM with the registered agents as tools, runs the requested agents, feeds their responses back, and repeats until the LLM answers without tools. That answer is the reply."""

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

    def run(self, input_message: InputMessage):
        """Run the reasoning engine for one user message.

        :param input_message: The input message to the reasoning engine.
        """
        ctx = self.context.build(self.session, input_message)
        self.output_message.actions.append("Reasoning the message..")
        self.output_message.push_update()
        tools = [agent.to_llm_format() for agent in self.agents.values()]

        for _ in range(self.max_iterations):
            response: LLMResponse = self.llm.chat_completions(
                messages=self.policy.apply(ctx), tools=tools
            )
            logger.info(f"LLM Response: {response}")

            if not response.status:
                self._fail(response)
                break

            if response.tool_calls:
                ctx.append(
                    ContextMessage(
                        content=response.content,
                        tool_calls=response.tool_calls,
                        role=RoleTypes.assistant,
                    )
                )
                if response.content:
                    self._show_text(response.content)
                for tool_call in response.tool_calls:
                    ctx.append(self._run_tool(tool_call))
                continue

            self._reply(ctx, response.content)
            break
        else:
            self._reply(ctx, MAX_ITERATIONS_REPLY)

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

        return ContextMessage(
            content=agent_response.__str__(),
            tool_call_id=tool_call["id"],
            role=RoleTypes.tool,
        )

    def _show_text(self, text: str):
        self.output_message.content.append(
            TextContent(text=text, status=MsgStatus.success, agent_name="assistant")
        )
        self.output_message.push_update()

    def _reply(self, ctx: List[ContextMessage], text: str):
        """End the turn: the reply is shown and saved as the last assistant message."""
        if text:
            ctx.append(ContextMessage(content=text, role=RoleTypes.assistant))
            self.output_message.content.append(
                TextContent(text=text, status=MsgStatus.success, agent_name="assistant")
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
