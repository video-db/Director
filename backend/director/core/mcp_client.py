import json
import logging
import shutil
from typing import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, get_default_environment
from mcp.client.sse import sse_client
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

    @asynccontextmanager
    async def create_session(
        self,
        server_name,
        config
    ) -> AsyncGenerator[ClientSession, None]:
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not found in configuration.")

        if config.get("transport") == "stdio":
            if not config.get("command") or not config.get("args"):
                raise ValueError(
                    f"Command and args are required for stdio transport: {server_name}"
                )

            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env={**get_default_environment(), **config.get("env", {})},
            )

            logger.info(f"{server_name}: Initializing stdio transport with {server_params}")

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await session.initialize()
            logger.info(f"{server_name}: Connected to server using stdio transport.")

            try:
                yield session
            finally:
                logger.debug(f"{server_name}: Closing session.")

        elif config.get("transport") == "sse":
            if not config.get("url"):
                raise ValueError(f"URL is required for SSE transport: {server_name}")

            async with sse_client(config["url"]) as (read_stream, write_stream):
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )

                logger.info(f"{server_name}: Connected to server using SSE transport.")

                try:
                    yield session
                finally:
                    logger.debug(f"{server_name}: Closing session.")

        else:
            raise ValueError(f"Unsupported transport: {config.get('transport')}")

    async def close(self) -> None:
        """Closes all managed sessions and releases resources."""
        await self.exit_stack.aclose()
        logger.info("MCPClient closed all sessions.")

    async def connect_to_server(self, name, config):
        async with self.create_session(name, config) as session:
            if not session:
                logger.error(f"Failed to connect to server: {name}")
                return []

            response = await session.list_tools()
            tools = response.tools
            for tool in tools:
                tool.server_name = name

            logger.info(f"Connected to {name} server with {len(tools)} tools.")
            self.mcp_tools = tools
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
        try:
            tool = next((t for t in self.mcp_tools if t.name == tool_name), None)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found in MCP tools.")

            config = self.servers.get(tool.server_name)
            if not config:
                raise ValueError(f"Server '{tool.server_name}' not found in config.")

            async with self.create_session(tool.server_name) as session:
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

