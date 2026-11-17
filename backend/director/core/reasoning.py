import logging
import time
from typing import List, Optional

from director.agents.base import BaseAgent, AgentStatus, AgentResponse
from director.core.context import ContextBuilder, ContextPolicy
from director.core.judge import ActionJudge, user_texts
from director.core.permissions import CallInfo, Decision, decide
from director.core.session import (
    ApprovalContent,
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

APPROVED_BY = {
    "read_only": "",
    "mode": "Full access",
    "chat": "Allowed for this chat",
    "judge": "Approved by the safety check",
}


def denial_text(reason: str) -> str:
    return (
        f"Not run: {reason} Don't retry the same action unchanged. "
        "Change the plan, or tell the user what you need."
    )


class ReasoningEngine:
    """The Reasoning Engine is the core class that directly interfaces with the user. It interprets natural language input in any conversation and orchestrates agents to fulfill the user's requests.

    Each turn it calls the LLM with the registered agents as tools, runs the requested agents, feeds their responses back, and repeats until the LLM answers without tools. That answer is the reply.

    A tool call that needs the user's approval pauses the turn: the approval is saved, the
    message is marked awaiting_approval, and the turn ends. `resume()` continues it later.
    """

    def __init__(
        self,
        session: Session,
        llm: BaseLLM,
        agents: List[BaseAgent],
        context: ContextBuilder = None,
        policy: ContextPolicy = None,
        max_iterations: int = 10,
        judge: Optional[ActionJudge] = None,
    ):
        """Initialize the ReasoningEngine.

        :param session: The session instance.
        :param llm: The LLM used for reasoning and summarization.
        :param agents: The agents offered to the LLM as tools.
        :param context: Builds the reasoning context for a turn.
        :param policy: Trims the context sent to the LLM.
        :param max_iterations: Max LLM calls before the turn is closed.
        :param judge: Auto mode's safety check; without it Auto asks like Ask mode.
        """
        self.session = session
        self.llm = llm
        self.agents = {agent.agent_name: agent for agent in agents}
        self.context = context or ContextBuilder()
        self.policy = policy or ContextPolicy()
        self.max_iterations = max_iterations
        self.judge = judge
        self.output_message = session.output_message

    def run(self, input_message: InputMessage):
        """Run the reasoning engine for one user message.

        :param input_message: The input message to the reasoning engine.
        """
        ctx = self.context.build(self.session, input_message)
        self.output_message.actions.append("Reasoning the message..")
        self.output_message.push_update()
        self._loop(ctx)

    def resume(self):
        """Continue a paused turn once every approval has a tool result in the context."""
        ctx = self.context.rebuild(self.session)
        self.output_message.status = MsgStatus.progress
        self.output_message.push_update()
        self._loop(ctx)

    def _loop(self, ctx: List[ContextMessage]):
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
                paused = False
                for tool_call in response.tool_calls:
                    result = self._handle(tool_call, ctx)
                    if result is None:
                        paused = True
                    else:
                        ctx.append(result)
                if paused:
                    self._pause()
                    break
                continue

            self._reply(ctx, response.content)
            break
        else:
            self._reply(ctx, MAX_ITERATIONS_REPLY)

        self.session.save_context_messages()
        self.session.save_permissions()

    def _handle(self, tool_call: dict, ctx) -> Optional[ContextMessage]:
        """Decide on one tool call: its tool message, or None when it waits for the user."""
        agent_name = tool_call["tool"]["name"]
        arguments = tool_call["tool"]["arguments"]
        agent = self.agents.get(agent_name)
        if agent is None:
            return self._tool_message(
                tool_call,
                AgentResponse(
                    status=AgentStatus.ERROR, message=f"Unknown agent: {agent_name}"
                ),
            )

        info = self.inspect(agent, arguments)
        decision = decide(agent_name, info, self.session.permissions, self._judge(ctx))
        self.session.permissions.record(decision)
        logger.info(
            f"{agent_name}: {decision.action} ({decision.source}) {decision.reason}"
        )

        if decision.action == "allow":
            return self.run_tool(tool_call, APPROVED_BY.get(decision.source, ""))
        if decision.action == "deny":
            self._show_text(f"Blocked: {decision.reason}", status=MsgStatus.error)
            return self._tool_message(
                tool_call,
                AgentResponse(
                    status=AgentStatus.ERROR, message=denial_text(decision.reason)
                ),
            )
        self._ask(tool_call, info, decision)
        return None

    def _judge(self, ctx):
        if self.judge is None:
            return None
        asked = user_texts(ctx)
        return lambda name, info: self.judge.review(name, info, asked)

    @staticmethod
    def inspect(agent: BaseAgent, arguments: dict) -> CallInfo:
        try:
            return agent.inspect(**arguments)
        except Exception:
            logger.exception(f"inspect failed for {agent.agent_name}")
            return CallInfo(
                preview=str(arguments),
                risks=["Director couldn't check this call."],
            )

    def run_tool(self, tool_call: dict, approved_by: str = "") -> ContextMessage:
        """Run the agent requested by a tool call and return its tool message."""
        agent_name = tool_call["tool"]["name"]
        arguments = tool_call["tool"]["arguments"]
        logger.info(f"Running {agent_name} agent with {arguments}")

        agent = self.agents[agent_name]
        agent.approved_by = approved_by
        self.output_message.actions.append(f"Running @{agent_name} agent")
        if agent_name not in self.output_message.agents:
            self.output_message.agents.append(agent_name)
        self.output_message.push_update()
        return self._tool_message(tool_call, agent.safe_call(**arguments))

    @staticmethod
    def _tool_message(tool_call: dict, response: AgentResponse) -> ContextMessage:
        return ContextMessage(
            content=response.__str__(),
            tool_call_id=tool_call["id"],
            role=RoleTypes.tool,
        )

    def _ask(self, tool_call: dict, info: CallInfo, decision: Decision):
        """Save the approval and show its card. The tool result comes when the user answers."""
        agent_name = tool_call["tool"]["name"]
        options = ["once", "chat", "deny"] if decision.offer_chat else ["once", "deny"]
        self.session.db.create_approval(
            approval_id=tool_call["id"],
            session_id=self.session.session_id,
            conv_id=self.session.conv_id,
            msg_id=self.output_message.msg_id,
            agent=agent_name,
            arguments=tool_call["tool"]["arguments"],
            reason=decision.reason,
            created_at=int(time.time()),
        )
        self.output_message.content.append(
            ApprovalContent(
                approval_id=tool_call["id"],
                agent_name=agent_name,
                preview=info.preview,
                language=info.language,
                reason=decision.reason,
                options=options,
                status=MsgStatus.success,
            )
        )
        self.output_message.push_update()

    def _pause(self):
        self.output_message.actions.append("Waiting for your approval")
        self.output_message.status = MsgStatus.awaiting_approval
        self.output_message.publish()

    def _show_text(self, text: str, status: MsgStatus = MsgStatus.success):
        self.output_message.content.append(
            TextContent(text=text, status=status, agent_name="assistant")
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
