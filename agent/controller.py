from agent.memory import MemoryManager
from agent.planner import call_llama_intent_parser
from agent.tools import CalculatorTool, OutletTool

# Controller ties together intent parsing, tool dispatch, and memory management
class ChatbotController:
    def __init__(self):
        # Initialize memory to track conversation context
        # ConversationBufferMemory stores history of user & bot turns for slot resolution
        self.memory = MemoryManager()
        # Tools encapsulate external APIs or functions for calculation and outlet queries
        self.calculator = CalculatorTool()
        self.outlet_tool = OutletTool()

    def handle_user_input(self, user_input: str) -> str:
        """
        Process a single user message end-to-end:
        1. Parse intent & slots via LLaMA 3.3-70B Instruct on OpenRouter
        2. Check memory for missing context
        3. Dispatch to appropriate tool or follow-up
        4. Save both user and bot messages to memory
        5. Return bot response
        """
        # 1. Parse intent and extract slots
        parsed = call_llama_intent_parser(user_input)

        response = ""

        # 2. Handle based on intent
        if parsed.intent == "calculate":
            # If expression slot is present, compute; else ask for it
            expr = parsed.slots.get("expression")
            if expr:
                # CalculatorTool wraps safe evaluation or external API
                result = self.calculator.evaluate(expr)
                response = f"The result of `{expr}` is {result}."
            else:
                response = "Sure—what expression would you like me to calculate?"

        elif parsed.intent in ("find_outlet", "get_opening_hours"):  # outlet-related
            # Ensure we have at least one slot (location or outlet)
            if parsed.slots:
                # OutletTool.query handles building the NL-to-SQL or API call
                response = self.outlet_tool.query(parsed.slots, parsed.intent)
            else:
                # If no slot, prompt for clarification
                response = "Which outlet or area are you interested in?"

        elif parsed.intent == "greeting":
            # Simple canned response for greetings
            response = "Hello! How can I help you today?"

        else:
            # Unknown or unhandled intents: ask for clarification
            response = "I’m not sure I understand. Could you clarify your request?"

        # 3. Persist conversation history for future context
        self.memory.add_user_message(user_input)
        self.memory.add_bot_message(response)

        # 4. Return the crafted response
        return response

    async def run(self, user, memory):
        # 1. Get the latest user message (assuming memory stores conversation history)
        user_message = memory.get_latest_message(user)
        if not user_message:
            return "I didn't receive any message from you."

        # 2. Parse intent and slots using the planner (LLM)
        parsed = call_llama_intent_parser(user_message)
        intent = parsed.intent
        slots = parsed.slots

        # 3. Route based on intent
        if intent == "greeting":
            return "Hello! How can I help you today?"

        elif intent == "find_outlet":
            location = slots.get("location", "unknown location")
            # TODO: Call your outlet search logic here
            return f"Looking up outlets in {location}... (not yet implemented)"

        elif intent == "get_opening_hours":
            outlet = slots.get("outlet", "unknown outlet")
            # TODO: Call your opening hours logic here
            return f"Checking opening hours for {outlet}... (not yet implemented)"

        elif intent == "calculate":
            expression = slots.get("expression")
            if not expression:
                return "Please provide a math expression to calculate."
            # TODO: Call your calculator API or logic here
            return f"Calculating: {expression}... (not yet implemented)"

        elif intent == "unknown":
            return "Sorry, I couldn't understand your request. Can you rephrase?"

        else:
            return f"Intent '{intent}' is not supported yet."

# Example instantiation and loop (CLI style):
# controller = ChatbotController()\#
# while True:
#     user_text = input("User: ")
#     bot_reply = controller.handle_user_input(user_text)
#     print(f"Bot: {bot_reply}")
