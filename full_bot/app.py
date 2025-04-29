import chainlit as cl
import os
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from typing import Optional, Dict

# Disable tracing if set in environment
set_tracing_disabled(os.getenv("DISABLE_TRACING", "True") == "True")

# Load environment variables
load_dotenv()
api_key = os.getenv("api_key")
github_client_id = os.getenv("OAUTH_GITHUB_CLIENT_ID")
github_client_secret = os.getenv("OAUTH_GITHUB_CLIENT_SECRET")
google_client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")

# Check if environment variables are loaded correctly
print("API Key: ", api_key)
print("GitHub Client ID: ", github_client_id)
print("Google Client ID: ", google_client_id)

# ✅ Custom timeout configuration for HTTPX
# No proxies argument

# ✅ Setup OpenAI Provider with custom client
provider = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    # Ensure AsyncOpenAI can accept this if it's designed that way
)

# Starter messages
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="⚡ Build Your Dream Morning",
            message="Let's create your perfect morning routine! 🌞 What time do you wake up, and what activities energize you most?",
            icon="/public/sun.svg",
        ),
        cl.Starter(
            label="🧠 Superconductors for Kids",
            message="Explain superconductors to me like I'm five years old! Use easy words and examples 🧸.",
            icon="/public/brain.svg",
        ),
        cl.Starter(
            label="💻 Daily Cold Email",
            message="How to write a cold email as a developer seeking a job interview. Create a natural, human-sounding email! 📧",
            icon="/public/code.svg",
        ),
        cl.Starter(
            label="💌 Invite a Friend Casually",
            message="Draft a short, casual text inviting a friend to be my plus-one at a wedding next month. Keep it chill and friendly!",
            icon="/public/heart.svg",
        ),
    ]

# Initialize conversation history
@cl.on_chat_start
async def chat_handler():
    cl.user_session.set("conversation_history", [])
    await cl.Message(content= f"Welcome to chatbot,How Can I Help You Today!!!").send()

# Handle incoming messages and "continue without an account"
@cl.on_message
async def handle_message(message: cl.Message):
    # Check for the "continue without an account" case
    if "continue without an account" in message.content.lower():
        await cl.Message(content="You are now using the chatbot without logging in. Feel free to ask anything!").send()
        return

    print("The response of chatbot is running", "-" * 22)
    conversation_history = cl.user_session.get("conversation_history")
    conversation_history.append({"role": "user", "content": message.content})

    agent = Agent(
        name="An Assistant",
        instructions="You are a helpful assistant that can answer questions.",
        model=OpenAIChatCompletionsModel(model="gemini-1.5-flash", openai_client=provider),
    )

    try:
        result = await Runner.run(agent, input=conversation_history)
        conversation_history.append({"role": "assistant", "content": result.final_output})

        await cl.Message(content=f"AI: {result.final_output}").send()
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

# OAuth callback functions
@cl.oauth_callback
async def login_github(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
    print("Logging in through GitHub", "="*9)
    print(f"Provider ID: {provider_id}")
    print(f"Token: {token}")
    print(f"Raw user data: {raw_user_data}")

    try:
        # Implement your login verification logic here
        return default_user
    except Exception as e:
        print(f"GitHub login failed: {e}")
        return None

@cl.oauth_callback
async def login_google(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
    print("Logging in through Google", "="*9)
    print(f"Provider ID: {provider_id}")
    print(f"Token: {token}")
    print(f"Raw user data: {raw_user_data}")

    try:
        # Implement your login verification logic here
        return default_user
    except Exception as e:
        print(f"Google login failed: {e}")
        return None

# Password authentication example
@cl.password_auth_callback
async def login_page(username: str, password: str) -> Optional[cl.User]:
    # Example: Simulating user authentication with hardcoded credentials
    if (username, password) == ("admin@gmail.com", "admin1234"):
        # Success message when login is successful
        return cl.User(
            identifier="admin", 
            metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        # Failed login message with a friendly message and suggestion to try again
        await cl.Message(content="🚫 **Login Failed**: Incorrect username or password. Please try again!").send()
        return None

