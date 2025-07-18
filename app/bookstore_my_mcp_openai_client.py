import asyncio
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import AIMessage
from converter import convert_addable_values_dict

# Load environment variables from .env file
load_dotenv()

# Verify that the API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

## response with gpt-4o
## ❯ uv run bookstore_mcp_client.py
## The book with ID 4 has multiple authors:
## 1. First Name 10 Last Name 10
## 2. First Name 11 Last Name 11
## 3. First Name 12 Last Name 12
## 4. First Name 13 Last Name 13

## gpt-4.1-nano is not good at using tools; it is 25x cheaper than gpt-4o
## A: The book with ID 4 is titled "Book 4". However, based on the provided information, I do not have
## the details of the author of this book. Would you like me to look for the author by other means or
## check for additional information?

## gpt-4o-mini is 16x cheaper than gpt-4o
## A: The book with ID 4 has multiple authors:
## 1. **First Name 10 Last Name 10**
## 2. **First Name 11 Last Name 11**
## 3. **First Name 12 Last Name 12**
## If you need more details or information, feel free to ask!

## Example API call to get book details
## curl -X GET "https://fakerestapi.azurewebsites.net/api/v1/Authors/authors/books/4" -H  "accept: text/plain; v=1.0"

# Initialize the OpenAI Chat model
model = ChatOpenAI(
    model="gpt-4o-mini"
)

async def main():
    # Define MCP server configurations
    server_configs = {
        "bookstore": {
            "url": "http://localhost:8500/sse",
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
        print(f"Response: {json.dumps(convert_addable_values_dict(response))}")


        final_ai_message = next(
            (m for m in reversed(response.get('messages')) if isinstance(m, AIMessage) and m.content.strip()),
            None
        )
        print(final_ai_message.content)


if __name__ == "__main__":
    asyncio.run(main())
