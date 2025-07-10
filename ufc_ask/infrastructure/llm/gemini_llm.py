from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

#LLM usada
class GeminiLLM:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", convert_system_message_to_human=True)

    def generate(self, prompt: str) -> str:
        try:
            response: AIMessage = self.model.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
