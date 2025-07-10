from fastapi import FastAPI
from pydantic import BaseModel

from agent.memory import MemoryManager
from agent.controller import ChatbotController

app = FastAPI()

# Module‐level instances
memory = MemoryManager()
controller = ChatbotController()

# Define the request body schema
class Message(BaseModel):
    user: str
    content: str

@app.post("/chat")
async def chat(msg: Message):
    """
    Handle incoming chat messages by delegating to the ChatbotController.
    """
    # Call the controller's run method (async)
    response = await controller.run(msg.user, memory)
    return {"response": response}