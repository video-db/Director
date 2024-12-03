## ⚙️ Architecture Overview
Director's architecture brings together:

**Backend Reasoning Engine:** Handles workflows and decision-making. Check out the <a href="https://github.com/video-db/Director/tree/main/backend" target="_blank" rel="noopener noreferrer">backend folder</a> in director codebase. 
**Chat-Based UI:** Engage with your media library conversationally. Check <a href="https://github.com/video-db/videodb-chat" target="_blank" rel="noopener noreferrer">videodb-chat</a> for the source code.
**Video Player:** Advanced playback and interaction tools. Check <a href="https://github.com/video-db/videodb-player" target="_blank" rel="noopener noreferrer">videodb-player</a> for the details about the multi-platform video player.
- **Collection View:** Organize and browse your media effortlessly.

![Director architecture](https://github.com/user-attachments/assets/9afb2783-66db-4899-9308-03cbd12e74d7)

## Reasoning Engine

The Reasoning Engine is the core component that directly interfaces with the user. It interprets natural language input in any conversation and orchestrates agents to fulfill the user's requests. The primary functions of the Reasoning Engine are:

* **Maintain Context of Conversational History:** Manage memory, context limits, input, and output experiences to ensure coherent and context-aware interactions.
* **Natural Language Understanding (NLU):** Uses LLMs of your choice to have understanding of the task. 
* **Intelligent Reference Deduction:** Intelligently deduce references to previous messages, outputs, files, agents, etc., to provide relevant and accurate responses.
* **Agent Orchestration:** Decide on agents and their workflows to fulfill requests. Multiple strategies can be employed to create agent workflows, such as step-by-step processes or chaining of agents provided by default.
* **Final Control Over Conversation Flow:** Maintain ultimate control over the flow of conversation with the user, ensuring coherence and goal alignment.

### **See It in Action**
The Reasoning Engine works in tandem with the chat-based UI, making video interaction intuitive and efficient. For example:  
- **Input**: "Create a clip of the funniest scene in this video and share it on Slack."  
- **Output**: The engine orchestrates upload, scene detection, clipping, and sharing agents to deliver results seamlessly. Watch the video [here](https://www.youtube.com/watch?v=fxhMgQf7v8s&list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw&index=3)

For a closer look, check out the detailed architecture diagram below:  
![Reasoning Engine Architecture](https://github.com/user-attachments/assets/13a92f0d-5b66-4a95-a2d4-0b73aa359ca6)


## Agents

An Agent is an autonomous entity that performs specific tasks using available tools. Agents define the user experience and are unique in their own way. Some agents can make the conversation fun while accomplishing tasks, similar to your favorite barista. Others might provide user experiences like a video player, display images, collections of images, or engage in text-based chat. Agents can also have personalities. We plan to add multiple agents for the same tasks but with a variety of user experiences.



For example, the task "Give me a summary of this video" can be accomplished by choosing one of the summary agents:

* "PromptSummarizer": This agent asks you for prompts that can be used for generating a summary. You have control and freedom over the style in each interaction.
* "SceneSummarizer": This agent uses scene descriptions, audio, etc., to generate a summary in a specific format using its internal prompt.



### Key aspects of Agents include:

* **Task Autonomy:** Agents perform tasks independently, utilizing tools to achieve their objectives.
* **Unique User Experiences (UX):** Each agent offers a distinct user experience, enhancing engagement and satisfaction. Multiple agents for the same task offer personalized interactions and cater to different user preferences like loading a specific UI or just a text message.
* **Standardized Agent Interface:** Agents communicate with the Reasoning Engine through a common API or protocol, ensuring consistent integration and interaction.

### Agent Examples

  1. Highlight Creator: <a href="https://www.youtube.com/watch?v=Dncn_0RWrro&list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw&index=11" target="_blank" rel="noopener noreferrer">link</a>
  2. Text to Movie: <a href="https://www.youtube.com/watch?v=QpnRxuEBDCc&list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw&index=2" target="_blank" rel="noopener noreferrer">link</a>
  3. Video Search: <a href="https://www.youtube.com/watch?v=kCiCI2KCnC8&list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw&index=4" target="_blank" rel="noopener noreferrer">link</a>


## Tools

Tools are functional building blocks that can be created from any library and used within agents. They are the functions that enable agents to perform their tasks. For example, we have created an upload tool that is a wrapper around the videodb upload function, another one is an index function with parameters.

### Key aspects of Tools include:

* Functional Building Blocks: Serve as modular functions that agents can utilize to perform tasks efficiently.
* Wrapper Functions: Act as wrappers for existing functions or libraries, enhancing modularity and reusability.

