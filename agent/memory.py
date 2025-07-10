from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_to_dict, messages_from_dict
import json

class MemoryManager:
    """
    Wrapper around LangChain ConversationBufferMemory to manage conversational state.

    Attributes:
        memory: LangChain ConversationBufferMemory instance storing messages.
    """
    def __init__(self, memory_key: str = "chat_history"):
        # use return_messages to preserve message objects for replay or serialization
        self.memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)

    def add_user_message(self, text: str):
        """Add a user message to memory."""
        self.memory.chat_memory.add_user_message(text)

    def add_bot_message(self, text: str):
        """Add a bot message to memory."""
        self.memory.chat_memory.add_ai_message(text)

    def get_history(self) -> list:
        """Get the list of messages stored in memory."""
        # returns list of message objects
        return self.memory.chat_memory.messages

    def load_memory(self, filepath: str):
        """Load memory from a JSON file containing serialized messages."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        msgs = messages_from_dict(data)
        self.memory.chat_memory.messages = msgs

    def save_memory(self, filepath: str):
        """Save current memory to a JSON file for persistence."""
        data = messages_to_dict(self.memory.chat_memory.messages)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def clear(self):
        """Clear the memory buffer."""
        self.memory.clear()

# Example usage:
# mm = MemoryManager()
# mm.add_user_message("Hello, is there an outlet in PJ?")
# mm.add_bot_message("Yes, which outlet?")
# print(mm.get_history())
