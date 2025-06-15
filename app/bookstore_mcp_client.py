import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import AIMessage

os.environ["OPENAI_API_KEY"] = "YOUR-KEY-HERE"

# Initialize the OpenAI Chat model
model = ChatOpenAI(
    model="gpt-4o"
)

async def main():
    # Define MCP server configurations
    server_configs = {
        "bookstore": {
            "url": "http://localhost:8000/sse",
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

        agent = create_react_agent(model, tools, prompt=prompt)

        # Run the agent with a sample input
        response = await agent.ainvoke({"messages": "Who is the author of the book with ID 4?"})

        final_ai_message = next(
            (m for m in reversed(response.get('messages')) if isinstance(m, AIMessage) and m.content.strip()),
            None
        )
        print(final_ai_message.content)


if __name__ == "__main__":
    asyncio.run(main())
