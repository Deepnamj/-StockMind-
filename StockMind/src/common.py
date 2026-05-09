# common.py
# Provides a shared helper that returns a configured LLM instance.
# Originally used Anthropic Claude — converted to use Google Gemini.
#
# Setup:
#   1. pip install langchain-google-genai python-dotenv
#   2. Add GEMINI_API_KEY=your_key_here to your .env file

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini via LangChain
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root.
# This makes GEMINI_API_KEY available via os.getenv() below.
load_dotenv()


def get_llm() -> BaseChatModel:
    """
    Returns a configured Gemini LLM instance for use across the project.

    Reads GEMINI_API_KEY from the environment (or .env file).
    Raises a clear error if the key is missing so misconfiguration is
    caught early rather than producing a confusing API error later.

    Returns:
        BaseChatModel: A LangChain-compatible Gemini chat model instance.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing credentials: Please set the GEMINI_API_KEY environment variable "
            "in your .env file or shell before running."
        )

    # Return a Gemini 1.5 Flash instance.
    # - gemini-1.5-flash is fast, cost-efficient, and supports function/tool calling
    #   which is required for the MCP tool-binding in graph.py.
    # - The api_key is passed explicitly so it doesn't rely on ADC (Application
    #   Default Credentials), making it easier to run locally.
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
    )