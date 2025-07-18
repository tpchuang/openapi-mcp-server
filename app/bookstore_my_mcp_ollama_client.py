import asyncio
import json
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import AIMessage
from converter import convert_addable_values_dict

## model="llama3.2:3b", doesn't know how to use tools
## deepseek -r1:14b and -v2:16b don't support tools
## llama3.1:8b can't find the right tool.
## model="granite3.3:8b" found the reight toolm but it didn't use tool, it just generates mock data from the schema
## model="llama3-groq-tool-use:8b" doesn't make api call

# Load environment variables from .env file
load_dotenv()

# Initialize the Ollama Chat model
model = ChatOllama(
    model="llama3.1:8b",
    base_url=os.getenv("OLLAMA_SERVER", "http://localhost:11434")
)

async def main():
    # Define MCP server configurations
    server_configs = {
        "bookstore": {
            # read MCP_SERVER_PORT from environment variable
            "url": f"http://localhost:{os.getenv('MCP_SERVER_PORT', 8000)}/sse",
            "transport": "sse",
            "verify_ssl": False
        }
    }
    # Multiple MCP servers can be configured.

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that interacts with a bookstore API to answer questions."),
        ("human", "{messages}")
    ])

    # Connect to MCP servers
    async with MultiServerMCPClient(server_configs) as client:
        tools = client.get_tools()
        # print(f"Available tools: {tools}")

        agent = create_react_agent(model, tools, prompt=prompt)

        # Run the agent with a sample input
        response = await agent.ainvoke({"messages": "Who is the author of the book with ID 4?"})
        # the type is langgraph.pregel.io.AddableValuesDict
        # print(f"Response type: {type(response)}")
        print(f"Response: {json.dumps(convert_addable_values_dict(response))}")

        final_ai_message = next(
            (m for m in reversed(response.get('messages')) if isinstance(m, AIMessage) and m.content.strip()),
            None
        )
        print(final_ai_message.content)


if __name__ == "__main__":
    asyncio.run(main())
