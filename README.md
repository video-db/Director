<!-- PROJECT SHIELDS -->
<!--
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Website][website-shield]][website-url]
[![Discord][discord-shield]][discord-url]

<!-- PROJECT LOGO -->
<img src="https://github.com/user-attachments/assets/78f5eead-d390-4b0b-a8bc-0017e6827c98" alt="logo">

<p align="center">
<p align="center">
        <a href="https://render.com/deploy?repo=https://github.com/video-db/Director" target="_blank" rel="nofollow">
                <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
        </a>
        <a href="https://railway.app/template/QJbo7o" target="_blank" rel="nofollow">
                <img src="https://railway.app/button.svg" alt="Deploy on Railway">
        </a>
        </p>



  <p align="center">
    Intelligent agents for your video library
    <br />
    <a href="https://www.youtube.com/playlist?list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw"><strong>View Demo »</strong></a>
    <br />
    <br />
    <a href="https://github.com/video-db/Director/issues/new?assignees=&labels=bug&projects=&template=bug_report.yml">Report Bug</a>
    ·
    <a href="https://github.com/video-db/Director/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.yml">Request Feature</a>
    ·
    <a href="https://github.com/video-db/Director/issues/new?assignees=&labels=enhancement&projects=&template=agent_request.yml">New Agent Request</a>
  </p>
</p>
<br/>

<!-- ABOUT THE PROJECT -->

##  🧐 What is The Director?

The Director is an AI-powered framework that lets you interact with your video and audio collections using natural language. Forget complex tools—just tell The Director what you want, and it gets it done.

Whether you’re working with social media clips, lectures, movies, YouTube videos, or any other content, The Director enables you to:

- Summarize videos in seconds.
- Search for specific moments.
- Create clips instantly.
- Add overlays, generate thumbnails, and much more.
All powered by VideoDB’s scalable ["video-as-data"](https://videodb.io/video-as-data) infrastructure.

For example, a simple command like:
`Upload this video and send the highlights to my Slack,`
sets everything in motion.

Built with flexibility in mind, The Director is perfect for developers, creators, and teams looking to harness AI to simplify media workflows and unlock new possibilities. 📺 [Watch: Intro video](https://console.videodb.io/player?url=https://stream.videodb.io/v3/published/manifests/26b4143c-ed97-442a-96ae-19b53eb3bb46.m3u8)



<!-- Intro Video -->


https://github.com/user-attachments/assets/33e0e7b4-9eb2-4a26-8274-f96c2c1c3a48



<br/>

## ⭐️ Key Features
### 🤖Build Smart Video Agents
Create custom AI agents that handle tedious tasks for you:

- Summarize videos in seconds.
- Search and index your media library.
- Organize and clip your content effortlessly.
### 🎨 A New Way to Interact
Experience a sleek, chat-based interface with built-in video playback and intuitive controls. It’s like having a personal assistant for your media.

### 🔍 Smarter Media Analysis
Connect seamlessly with powerful AI tools like LLMs, databases, and GenAI APIs, while VideoDB ensures your video infrastructure is reliable and scalable.

### 🧩 Customizable and Flexible
Easily add new features and tools to your workflow. Whether you want to run it locally or on your cloud, The Director adapts to your needs.

<br/>

## ⚙️ Architecture Overview
Director's architecture brings together:

Backend Reasoning Engine: Handles workflows and decision-making.
Chat-Based UI: Engage with your media library conversationally.
Video Player: Advanced playback and interaction tools.
Collection View: Organize and browse your media effortlessly.

  ![Director architecture](https://github.com/user-attachments/assets/9afb2783-66db-4899-9308-03cbd12e74d7)
  
## 🧠 **Reasoning Engine**

At the heart of The Director is its **Reasoning Engine**, a powerful core that drives intelligent decision-making and dynamic workflows. It acts as the brain behind the agents, enabling them to process commands, interact with data, and deliver meaningful outputs.

### **How It Works**
- **Contextual Understanding**: The engine analyzes user inputs and maintains context, ensuring smooth and coherent interactions with agents.  
- **Dynamic Agent Orchestration**: Based on the user’s needs, it identifies and activates the right agents to complete tasks efficiently.  
- **Modular Processing**: Tasks are broken into smaller steps, allowing agents to collaborate and deliver accurate results in real time.

### **Key Capabilities**
- **Multi-Agent Coordination**: Seamlessly integrates multiple agents to handle complex workflows, such as summarizing, editing, and searching videos.  
- **Real-Time Updates**: Provides live progress and feedback as tasks are being completed.  
- **Extensible Design**: Easily adaptable to include custom logic or connect to external APIs for more advanced capabilities.

### **See It in Action**
The Reasoning Engine works in tandem with the chat-based UI, making video interaction intuitive and efficient. For example:  
- **Input**: "Create a clip of the funniest scene in this video and share it on Slack."  
- **Output**: The engine orchestrates upload, scene detection, clipping, and sharing agents to deliver results seamlessly.

For a closer look, check out the detailed architecture diagram below:  
![Reasoning Engine Architecture](https://github.com/user-attachments/assets/13a92f0d-5b66-4a95-a2d4-0b73aa359ca6)

Explore how the Reasoning Engine powers The Director to simplify and supercharge your media workflows.



## 🏃 Getting Started
📺 [Watch: Setup video](https://console.videodb.io/player?url=https://stream.videodb.io/v3/published/manifests/fe85e051-5dfb-4409-8033-3963d8bde37a.m3u8)

### Prerequisites

- Python 3.9 or higher
- Node.js 22.8.0 or higher
- npm

### Installation

**1. Clone the repository:**

``` bash
git clone https://github.com/video-db/Director.git
cd Director
```

**2. Run the setup script:**

```bash
./setup.sh
```

> This script will:
> - Install Node.js 22.8.0 using nvm
> - Install Python and pip
> - Set up virtual environments for both frontend and backend.



**3. Configure the environment variables:**

Edit the `.env` files to add your API keys and other configuration options.

### Supported platforms: 
- Mac
- Linux
- Windows (WSL)

## 💬 Running the Application

To start both the backend and frontend servers:

```bash
make run
```

- Backend: `http://127.0.0.1:8000`

- Frontend: `http://127.0.0.1:8080`

For specific tasks:

- Backend only: `make run-be`

- Frontend only: `make run-fe`



<!-- CONTRIBUTING -->

## 📘 Creating a New Agent
To create a new agent in Director, follow these steps:

1. **Copy the template**: 
Duplicate `sample_agent.py` in `Director/backend/director/agents/` and rename it.

2. **Update class details**:
   - Rename the class.
   - Update `agent_name` and `description`

3. **Implement logic**:
   - Update parameters and `docstring`
   - Implement your agent's logic
   - Update the run() method.

4. **Handle output and status updates**:
   - Use appropriate content types (TextContent, VideoContent, ImageContent, SearchResultContent)
   - Update `self.output_message.actions` for progress indicators
   - Use `push_update()` to emit progress events
   - Set content status (progress, success, error) and messages

5. **Implement error handling**:
   - Set error status and messages if issues occur

6. **Finalize the response**:
   - Call `self.output_message.publish()` to emit final state and persist session
   - Return an `AgentResponse` with result, message, and data

7. **Register the agent**:
   - Import your new agent class in `Director/backend/director/handler.py`
   - Add it to the `self.agents` list in `ChatHandler`

Remember to consider creating reusable tools if your agent's functionality could be shared across multiple agents.


## 📖 Documentation

### Serve Locally
To serve the documentation on port 9000:

```bash
source backend/venv/bin/activate  
make install-be
mkdocs serve -a localhost:9000
```

To build the documentation:

```bash
mkdocs build
```



## 🤝 Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[discord-shield]: https://img.shields.io/badge/dynamic/json?style=for-the-badge&url=https://discord.com/api/invites/py9P639jGz?with_counts=true&query=$.approximate_member_count&logo=discord&logoColor=blue&color=green&label=discord
[discord-url]: https://discord.com/invite/py9P639jGz
[stars-shield]: https://img.shields.io/github/stars/video-db/Director.svg?style=for-the-badge
[stars-url]: https://github.com/video-db/Director/stargazers
[issues-shield]: https://img.shields.io/github/issues/video-db/Director.svg?style=for-the-badge
[issues-url]: https://github.com/video-db/Director/issues
[website-shield]: https://img.shields.io/website?url=https%3A%2F%2Fvideodb.io%2F&style=for-the-badge&label=videodb.io
[website-url]: https://videodb.io/


