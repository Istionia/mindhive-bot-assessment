import os
import json
from typing import Dict, Any
import openai
from pydantic import BaseModel, ValidationError, validator
from openai import OpenAI

# Configure OpenRouter (Meta LLaMA 3.3 70B Instruct)
# Set your OpenRouter API key in environment: OPENROUTER_API_KEY
openai.api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
)

# OpenRouter uses /chat/completions path
openai.api_type = "open_ai"
openai.api_version = None

# Prompt template for LLaMA 3.3-70B Instruct JSON parsing
LLAMA_INTENT_PROMPT = '''
You are an AI assistant that extracts structured intent and slot data from natural language queries.
Respond ONLY in valid JSON format:
{
  "intent": "<intent_name>",
  "slots": {
    "<slot1>": "...",
    "<slot2>": "..."
  }
}

Supported intents:
- find_outlet
- get_opening_hours
- calculate
- greeting
- unknown

Examples:

User: "Where's the ZUS outlet in Petaling Jaya?"
{
  "intent": "find_outlet",
  "slots": {
    "location": "Petaling Jaya"
  }
}

User: "SS2 outlet opening hours?"
{
  "intent": "get_opening_hours",
  "slots": {
    "outlet": "SS2"
  }
}

User: "What is 12 * (5 + 2)?"
{
  "intent": "calculate",
  "slots": {
    "expression": "12 * (5 + 2)"
  }
}

Now parse the following user input.

User: "{user_input}"
'''

class ParsedIntent(BaseModel):
    intent: str
    slots: Dict[str, Any]

    @validator('intent')
    def validate_intent(cls, v):
        allowed = {'find_outlet','get_opening_hours','calculate','greeting','unknown'}
        if v not in allowed:
            raise ValueError(f"Invalid intent: {v}")
        return v


def call_llama_intent_parser(user_input: str) -> ParsedIntent:
    """
    Sends a prompt to Meta-LLaMA 3.3-70B Instruct via OpenRouter to parse intent and slots.
    Returns a validated ParsedIntent object.
    Falls back to intent='unknown' on any errors.
    """
    prompt = LLAMA_INTENT_PROMPT.format(user_input=user_input)
    try:
        resp = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",  # OpenRouter model identifier
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content
        if content is None:
            raise ValueError("No content returned from LLM")
        content = content.strip()
        # Load JSON
        data = json.loads(content)
        # Validate
        parsed = ParsedIntent(**data)
        return parsed
    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        # On any parsing/validation error, return unknown intent
        return ParsedIntent(intent="unknown", slots={})

# Example usage:
# parsed = call_llama_intent_parser("Is the SS2 outlet in PJ open now?")
# print(parsed.intent, parsed.slots)
