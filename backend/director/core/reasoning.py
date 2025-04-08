import logging
from typing import List


from director.agents.base import BaseAgent, AgentStatus, AgentResponse
from director.core.session import (
    Session,
    OutputMessage,
    InputMessage,
    ContextMessage,
    RoleTypes,
    TextContent,
    MsgStatus,
)
from director.llm.base import LLMResponse
from director.llm import get_default_llm


logger = logging.getLogger(__name__)


REASONING_SYSTEM_PROMPT = """
SYSTEM PROMPT: The Director (v1.2)

1. **Task Handling**:
   - Identify and select agents based on user input and context.
   - Provide actionable instructions to agents to complete tasks.
   - Combine agent outputs with user input to generate meaningful responses.
   - Iterate until the request is fully addressed or the user specifies "stop."

2. **Fallback Behavior**:
   - If a task requires a video_id but one is unavailable:
     - For Stream URLs (m3u8), external URLs (e.g., YouTube links, direct video links, or videos hosted on other platforms):
       - Use the upload agent to generate a video_id.
       - Immediately proceed with the original task using the newly generated video_id.

3. **Identity**:
   - Respond to identity-related queries with: "I am The Director, your AI assistant for video workflows and management."
   - Provide descriptions of all the agents.

4. **Agent Usage**:
   - Always prioritize the appropriate agent for the task:
     - Use summarize_video for summarization requests unless search is explicitly requested.
     - For external video URLs, automatically upload and process them if required for further actions (e.g., summarization, indexing, or editing).
     - Use stream_video for video playback.
     - Ensure seamless workflows by automatically resolving missing dependencies (e.g., uploading external URLs for a missing video_id) without additional user intervention.

5. **Clarity and Safety**:
   - Confirm with the user if a request is ambiguous.
   - Avoid sharing technical details (e.g., code, video IDs, collection IDs) unless explicitly requested.
   - Keep the tone friendly and vibrant.

6. **LLM Knowledge Usage**:
   - Do not use knowledge from the LLM's training data unless the user explicitly requests it.
   - If the information is unavailable in the video or context:
     - Inform the user: "The requested information is not available in the current video or context."
     - Ask the user: "Would you like me to answer using knowledge from my training data?"

7. **Agent Descriptions**:
   - When asked, describe an agent's purpose, and provide an example query (use contextual video data when available).

8. **Context Awareness**:
   - Adapt responses based on conversation context to maintain relevance.
    """.strip()

SUMMARIZATION_PROMPT = """
FINAL CUT PROMPT: Generate a concise summary of the actions performed by the agents based on their responses.

1. Provide an overview of the tasks completed by each agent, listing the actions taken and their outcomes.
2. Exclude individual agent responses from the summary unless explicitly specified to include them.
3. Ensure the summary is user-friendly, succinct and avoids technical jargon unless requested by the user.
4. If there were any errors, incomplete tasks, or user confirmations required:
   - Clearly mention the issue in the summary.
   - Politely inform the user: "If you encountered any issues or have further questions, please don't hesitate to reach out to our team on [Discord](https://discord.com/invite/py9P639jGz). We're here to help!"
5. If the user seems dissatisfied or expresses unhappiness:
   - Acknowledge their concerns in a respectful and empathetic tone.
   - Include the same invitation to reach out on Discord for further assistance.
6. End the summary by inviting the user to ask further questions or clarify additional needs.

"""


class ReasoningEngine:
    """The Reasoning Engine is the core class that directly interfaces with the user. It interprets natural language input in any conversation and orchestrates agents to fulfill the user's requests. The primary functions of the Reasoning Engine are:

    * Maintain Context of Conversational History: Manage memory, context limits, input, and output experiences to ensure coherent and context-aware interactions.
    * Natural Language Understanding (NLU): Uses LLMs of your choice to have understanding of the task.
    * Intelligent Reference Deduction: Intelligently deduce references to previous messages, outputs, files, agents, etc., to provide relevant and accurate responses.
    * Agent Orchestration: Decide on agents and their workflows to fulfill requests. Multiple strategies can be employed to create agent workflows, such as step-by-step processes or chaining of agents provided by default.
    * Final Control Over Conversation Flow: Maintain ultimate control over the flow of conversation with the user, ensuring coherence and goal alignment."""

    def __init__(
        self,
        input_message: InputMessage,
        session: Session,
    ):
        """Initialize the ReasoningEngine with the input message and session.

        :param input_message: The input message to the reasoning engine.
        :param session: The session instance.
        """
        self.input_message = input_message
        self.session = session
        self.system_prompt = REASONING_SYSTEM_PROMPT
        self.max_iterations = 10
        self.llm = get_default_llm()
        self.agents: List[BaseAgent] = []
        self.stop_flag = False
        self.output_message: OutputMessage = self.session.output_message
        self.summary_content = None
        self.failed_agents = []

    def register_agents(self, agents: List[BaseAgent]):
        """Register an agents.

        :param agents: The list of agents to register.
        """
        self.agents.extend(agents)

    def build_context(self):
        """Build the context for the reasoning engine it adds the information about the video or collection to the reasoning context."""
        input_context = ContextMessage(
            content=self.input_message.content, role=RoleTypes.user
        )
        if self.session.reasoning_context:
            self.session.reasoning_context.append(input_context)
        else:
            if self.session.video_id:
                video = self.session.state["video"]
                self.session.reasoning_context.append(
                    ContextMessage(
                        content=self.system_prompt
                        + f"""\nThis is a video in the collection titled {self.session.state["collection"].name} collection_id is {self.session.state["collection"].id} \nHere is the video refer to this for search, summary and editing \n- title: {video.name}, video_id: {video.id}, media_description: {video.description}, length: {video.length}"""
                    )
                )
            else:
                videos = self.session.state["collection"].get_videos()
                video_title_list = []
                for video in videos:
                    video_title_list.append(
                        f"\n- title: {video.name}, video_id: {video.id}, media_description: {video.description}, length: {video.length}, video_stream: {video.stream_url}"
                    )
                video_titles = "\n".join(video_title_list)
                images = self.session.state["collection"].get_images()
                image_title_list = []
                for image in images:
                    image_title_list.append(
                        f"\n- title: {image.name}, image_id: {image.id}, url: {image.url}"
                    )
                image_titles = "\n".join(image_title_list)
                self.session.reasoning_context.append(
                    ContextMessage(
                        content=self.system_prompt
                        + f"""\nThis is a collection of videos and the collection description is {self.session.state["collection"].description} and collection_id is {self.session.state["collection"].id} \n\nHere are the videos in this collection user may refer to them for search, summary and editing {video_titles}\n\nHere are the images in this collection {image_titles}"""
                    )
                )
            self.session.reasoning_context.append(input_context)

    def get_current_run_context(self):
        for i in range(len(self.session.reasoning_context) - 1, -1, -1):
            if self.session.reasoning_context[i].role == RoleTypes.user:
                return self.session.reasoning_context[i:]
        return []

    def remove_summary_content(self):
        for i in range(len(self.output_message.content) - 1, -1, -1):
            if self.output_message.content[i].agent_name == "assistant":
                self.output_message.content.pop(i)
                self.summary_content = None

    def add_summary_content(self):
        self.summary_content = TextContent(agent_name="assistant")
        self.output_message.content.append(self.summary_content)
        self.summary_content.status_message = "Consolidating outcomes..."
        self.summary_content.status = MsgStatus.progress
        self.output_message.push_update()
        return self.summary_content

    def run_agent(self, agent_name: str, *args, **kwargs) -> AgentResponse:
        """Run an agent with the given name and arguments.

        :param str agent_name: The name of the agent to run
        :param args: The arguments to pass to the agent
        :param kwargs: The keyword arguments to pass to the agent
        :return: The response from the agent
        """
        print("-" * 40, f"Running {agent_name} Agent", "-" * 40)
        print(kwargs, "\n\n")

        agent = next(
            (agent for agent in self.agents if agent.agent_name == agent_name), None
        )
        self.output_message.actions.append(f"Running @{agent_name} agent")
        self.output_message.agents.append(agent_name)
        self.output_message.push_update()
        return agent.safe_call(*args, **kwargs)

    def stop(self):
        """Flag the tool to stop processing and exit the run() thread."""
        self.stop_flag = True

    def step(self):
        """Run a single step of the reasoning engine."""
        status = AgentStatus.ERROR
        temp_messages = []
        max_tries = 1
        tries = 0

        while status != AgentStatus.SUCCESS:
            if self.stop_flag:
                break

            tries += 1
            if tries > max_tries:
                break
            print("-" * 40, "Context", "-" * 40)
            print(
                [message.to_llm_msg() for message in self.session.reasoning_context],
                "\n\n",
            )
            llm_response: LLMResponse = self.llm.chat_completions(
                messages=[
                    message.to_llm_msg() for message in self.session.reasoning_context
                ]
                + temp_messages,
                tools=[agent.to_llm_format() for agent in self.agents],
            )
            logger.info(f"LLM Response: {llm_response}")

            if not llm_response.status:
                self.output_message.content.append(
                    TextContent(
                        text=llm_response.content,
                        status=MsgStatus.error,
                        status_message="Error in reasoning",
                        agent_name="assistant",
                    )
                )
                self.output_message.actions.append("Failed to reason the message")
                self.output_message.status = MsgStatus.error
                self.output_message.publish()
                self.stop()
                break

            if llm_response.tool_calls:
                if self.summary_content:
                    self.remove_summary_content()

                self.session.reasoning_context.append(
                    ContextMessage(
                        content=llm_response.content,
                        tool_calls=llm_response.tool_calls,
                        role=RoleTypes.assistant,
                    )
                )
                for tool_call in llm_response.tool_calls:
                    agent_response: AgentResponse = self.run_agent(
                        tool_call["tool"]["name"],
                        **tool_call["tool"]["arguments"],
                    )
                    if agent_response.status == AgentStatus.ERROR:
                        self.failed_agents.append(tool_call["tool"]["name"])
                    self.session.reasoning_context.append(
                        ContextMessage(
                            content=agent_response.__str__(),
                            tool_call_id=tool_call["id"],
                            role=RoleTypes.tool,
                        )
                    )
                    print("-" * 40, "Agent Response", "-" * 40)
                    print(agent_response, "\n\n")
                    status = agent_response.status

            if not self.summary_content:
                self.add_summary_content()

            if (
                llm_response.finish_reason == "stop"
                or llm_response.finish_reason == "end_turn"
                or self.iterations == 0
            ):
                self.session.reasoning_context.append(
                    ContextMessage(
                        content=llm_response.content,
                        role=RoleTypes.assistant,
                    )
                )
                if self.iterations == self.max_iterations - 1:
                    # Direct response case
                    self.summary_content.status_message = "Here is the response"
                    self.summary_content.text = llm_response.content
                    self.summary_content.status = MsgStatus.success
                else:
                    self.session.reasoning_context.append(
                        ContextMessage(
                            content=SUMMARIZATION_PROMPT.format(
                                query=self.input_message.content
                            ),
                            role=RoleTypes.system,
                        )
                    )
                    summary_response = self.llm.chat_completions(
                        messages=[
                            message.to_llm_msg()
                            for message in self.get_current_run_context()
                        ]
                    )
                    self.session.reasoning_context.pop()
                    self.summary_content.text = summary_response.content
                    if self.failed_agents:
                        self.summary_content.status = MsgStatus.error
                    else:
                        self.summary_content.status = MsgStatus.success
                    self.summary_content.status_message = "Final Cut"
                self.output_message.status = MsgStatus.success
                self.output_message.publish()
                print("-" * 40, "Stopping", "-" * 40)
                self.stop()
                break

    def run(self, max_iterations: int = None):
        """Run the reasoning engine.

        :param int max_iterations: The number of max_iterations to run the reasoning engine
        """
        self.iterations = max_iterations or self.max_iterations
        self.build_context()
        self.output_message.actions.append("Reasoning the message..")
        self.output_message.push_update()

        it = 0
        while self.iterations > 0:
            self.iterations -= 1
            print("-" * 40, "Reasoning Engine Iteration", it, "-" * 40)
            if self.stop_flag:
                break

            self.step()
            it = it + 1

        self.session.save_context_messages()
        print("-" * 40, "Reasoning Engine Finished", "-" * 40)
