from __future__ import annotations
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

# ---------------------------------------------------------
# AICredits configuration
# ---------------------------------------------------------
AICREDITS_API_KEY = "YOUR_AICREDITS_TEST_API_KEY"
AICREDITS_BASE_URL = "https://api.aicredits.in/v1"
MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0

# ---------------------------------------------------------
# Chat model
# ---------------------------------------------------------
def get_chat_model() -> BaseLanguageModel:
    if not AICREDITS_API_KEY:
        raise RuntimeError("AICREDITS_API_KEY is required")
        
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        api_key="sk-live-03807af33958beab30d3de8aaf3b3f5ae1e7862398579c37474c6364ef744b73",
        base_url="https://api.aicredits.in/v1",
    )


"""
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key="sk-live-175b4dc4ca25a7cabf1eac6f3557c8c01ed32ca17eb473f09c58a3b832c4d9a8",
    base_url="https://api.aicredits.in/v1",
)
"""