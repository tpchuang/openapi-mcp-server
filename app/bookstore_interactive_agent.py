import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

os.environ["OPENAI_API_KEY"] = "YOUR-KEY-HERE"

model = ChatOpenAI(
    model="gpt-4o"
)

async def ainput(prompt: str = ""):
    """
    Async wrapper for input to allow non-blocking user input.
    """
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


def extract_assistant_reply(response):
    """
    Extract the assistant's reply from various possible response formats.
    """
    # If response is a dict-like with 'messages' key, process that list
    if isinstance(response, dict) or hasattr(response, 'get') and hasattr(response, '__getitem__'):
        messages = response.get('messages', None)
        if messages and isinstance(messages, list):
            for msg in reversed(messages):
                if msg.__class__.__name__ == "AIMessage" and getattr(msg, "content", None):
                    return msg.content
            for msg in reversed(messages):
                if hasattr(msg, "content") and getattr(msg, "content", None):
                    return msg.content
            return str(messages[-1])
    # If response is a list, process as before
    if isinstance(response, list):
        for msg in reversed(response):
            if msg.__class__.__name__ == "AIMessage" and getattr(msg, "content", None):
                return msg.content
        for msg in reversed(messages):
            if hasattr(msg, "content") and getattr(msg, "content", None):
                return msg.content
        return str(response[-1])
    # If response is a dict with 'content'
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    # If response has a 'content' attribute
    if hasattr(response, "content"):
        return response.content
    # Fallback
    return str(response)


async def main():
    """
    Main function to run the chatbot loop.
    Sets up the MCP client, loads tools, and handles user interaction.
    """
    server_configs = {
        "bookstore": {
            "url": "http://localhost:8000/sse",
            "transport": "sse",
            "verify_ssl": False
        }
    }

    async with MultiServerMCPClient(server_configs) as client:
        prompt = "You are a helpful assistant that interacts with a bookstore API to answer questions."
        tools = client.get_tools()
        agent = create_react_agent(model, tools)

        print("Welcome to the Bookstore Chatbot! Type 'exit' or 'quit' to end the conversation.")
        history = [{"role":"system", "content":prompt}]

        while True:
            user_input = await ainput("You: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("Goodbye!")
                break
            history.append({"role": "user", "content": user_input})
            try:
                response = await agent.ainvoke({"messages": history})
            except Exception as e:
                print("An error occurred while processing your request.")
                continue
            # Debug print to inspect the response structure
            if isinstance(response, list):
                for i, msg in enumerate(response):
                    print(f"msg[{i}] type: {type(msg)}, class: {msg.__class__.__name__}, content: {getattr(msg, 'content', None)}")
            assistant_reply = extract_assistant_reply(response)
            print(f"Bot: {assistant_reply}")
            history.append({"role": "assistant", "content": assistant_reply})


if __name__ == "__main__":
    asyncio.run(main())
