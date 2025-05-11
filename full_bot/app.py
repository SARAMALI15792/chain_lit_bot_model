import chainlit as cl
import os
import asyncio
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Runner
from dotenv import load_dotenv
from typing import Optional, Dict
import random
# Disable tracing if set in environment
set_tracing_disabled(os.getenv("DISABLE_TRACING", "True") == "True")

# Load environment variables
load_dotenv()
key1 = os.getenv("api_key")
github_client_id = os.getenv("OAUTH_GITHUB_CLIENT_ID")
github_client_secret = os.getenv("OAUTH_GITHUB_CLIENT_SECRET")


# Check if environment variables are loaded correctly
print("Google API Key: ", key1[:10] + "..." if key1 else "Not set")
print("GitHub Client ID: ", github_client_id)


# ✅ Setup OpenAI Provider with custom client
provider = AsyncOpenAI(
    api_key=key1,  # Default to OpenAI key
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Google Gemini API URL
)

# Random image generator
def get_random_image():
    return f"https://picsum.photos/seed/{random.randint(1, 1000)}/200/300"

# Define chat profiles
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="GPT-4.1",
            markdown_description="Welcome to GPT-4.1.",
            icon=get_random_image(),  # Using random image for the icon
        ),
        cl.ChatProfile(
            name="Gemini-1.5-Flash",
            markdown_description="Welcome to Gemini-1.5-Flash.",
            icon=get_random_image(),  # Using random image for the icon
        ),
    ]

# Starter suggestions
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="⚡ Build Your Dream Morning",
            message="Let's create your perfect morning routine! 🌞 What time do you wake up, and what activities energize you most?",
            icon=get_random_image(),
        ),
        cl.Starter(
            label="🧠 Superconductors for Kids",
            message="Explain superconductors to me like I'm five years old! Use easy words and examples 🧸.",
            icon=get_random_image(),
        ),
        cl.Starter(
            label="💻 Daily Cold Email",
            message="How to write a cold email as a developer seeking a job interview. Create a natural, human-sounding email! 📧",
            icon=get_random_image(),
        ),
        cl.Starter(
            label="💌 Invite a Friend Casually",
            message="Draft a short, casual text inviting a friend to be my plus-one at a wedding next month. Keep it chill and friendly!",
            icon=get_random_image(),
        ),
    ]

# Initialize conversation history
@cl.on_chat_start
async def start():
    cl.user_session.set("conversation_history", [])
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(content=f"🌟 Welcome to chatbot using the **{chat_profile}** How can I help you today?").send()

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
    
    # Check if Google API key is configured
    if not key1:
        await cl.Message(content="Error: Google API key not configured. Please set GOOGLE_API_KEY in your environment variables.").send()
        return
    msg = cl.Message(content="")
    await msg.send()

    
    agent = Agent(
        name="An Assistant",
        instructions="You are a helpful assistant that can answer questions.",
        model=OpenAIChatCompletionsModel(
            model="gemini-1.5-flash",
            openai_client=provider
        ),
    )

    try:
       
        result =Runner.run_streamed(agent, input=conversation_history)
     
        # Stream the response token by token
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
                token = event.data.delta
                await msg.stream_token(token)
                await asyncio.sleep(0.08)
        
        msg.content = result.final_output
        await msg.update()
        
        conversation_history.append({"role": "assistant", "content": result.final_output})
        cl.user_session.set("conversation_history", conversation_history)
        
    except Exception as e:
        await cl.Message(content=f"Error occurred while running the response: {str(e)}").send()

# OAuth callback functions
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    print(f"Provider: {provider_id}")
    print(f"User data: {raw_user_data}")
    return default_user

# Password authentication example
@cl.password_auth_callback
async def login_page(username: str, password: str) -> Optional[cl.User]:
    if (username, password) == ("admin@gmail.com", "admin1234"):
        return cl.User(
            identifier="admin", 
            metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        await cl.Message(content="🚫 **Login Failed**: Incorrect username or password. Please try again!").send()
        return None
