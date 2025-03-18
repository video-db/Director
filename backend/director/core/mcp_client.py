import json
import logging
import shutil
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from director.agents.base import AgentResponse, AgentStatus
from director.constants import MCP_SERVER_CONFIG_PATH

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


class MCPClient:
    def __init__(self):
        self.config_path = MCP_SERVER_CONFIG_PATH
        self.servers = self.load_servers()
        self.mcp_tools = []
        self.exit_stack = AsyncExitStack()

    def load_servers(self):
        with open(self.config_path, 'r') as file:
            return json.load(file).get('mcpServers', {})

    async def create_session(self, config):
        """Creates a new session for a given server config."""
        try:
            exec_path = shutil.which(config['command'])
            server_params = StdioServerParameters(
                command=exec_path if exec_path else config['command'], 
                args=config['args'],
                env=config.get('env')
            )
            logger.info(f"Initializing server with params: {server_params}")

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            
            return session
        except Exception as e:
            logger.error(f"Failed to create session. Error: {e}")
            return None

    async def connect_to_server(self, name, config):
        """Connects to an MCP server and retrieves tools."""
        session = await self.create_session(config)
        if not session:
            logger.error(f"Failed to connect to server: {name}")
            return []

        response = await session.list_tools()
        tools = response.tools
        for tool in tools:
            tool.server_name = name
        self.mcp_tools.extend(tools)
        
        logger.info(f"Connected to {name} server with {len(tools)} tools.")
        return tools

    async def initialize_all_servers(self):
        """Initialize all servers asynchronously."""
        all_tools = []
        for name, config in self.servers.items():
            tools = await self.connect_to_server(name, config)
            all_tools.extend(tools)
        logger.info(f"Loaded {len(all_tools)} tools from all servers.")
        return all_tools

    def mcp_tools_to_llm_format(self):
        """Converts MCP tools into an LLM-compatible format."""
        return [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in self.mcp_tools]

    def is_mcp_tool_call(self, name):
        """Checks if a given tool name exists in the registered MCP tools."""
        return any(tool.name == name for tool in self.mcp_tools)

    async def call_tool(self, tool_name, tool_args):
        """Calls an MCP tool by name with provided arguments, creating a new session each time."""
        try:
            tool = next((t for t in self.mcp_tools if t.name == tool_name), None)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found in MCP tools.")

            config = self.servers.get(tool.server_name)
            if not config:
                raise ValueError(f"Server '{tool.server_name}' not found in config.")

            session = await self.create_session(config)
            if not session:
                raise ValueError(f"Failed to create session for server '{tool.server_name}'.")

            logger.info(f"Calling {tool_name} with args {tool_args}")
            result = await session.call_tool(tool_name, tool_args)

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Tool call successful: {tool_name}",
                data={"content": result.content}
            )

        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Error calling tool '{tool_name}': {e}",
                data={}
            )
