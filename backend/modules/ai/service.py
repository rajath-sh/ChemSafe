import logging
import google.generativeai as genai
from core.config import settings

logger = logging.getLogger(__name__)

class AiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.is_configured = bool(self.api_key)
        
        if self.is_configured:
            genai.configure(api_key=self.api_key)
            # Use gemini-2.5-flash as the default fast and capable model
            self.model = genai.GenerativeModel('gemini-2.5-flash', system_instruction="You are a helpful AI assistant built into the ChemSafe IoT platform. ChemSafe is a chemical laboratory safety management platform. You help users answer questions about safety, the system, and general inquiries.")
        else:
            logger.warning("GEMINI_API_KEY is not configured in .env")

    def get_chat_response(self, message: str) -> str:
        if not self.is_configured:
            return "AI Assistant is not configured. Please add the GEMINI_API_KEY to the backend .env file."
        
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            logger.exception("Failed to generate AI response")
            return f"I encountered an error while trying to process your request. ({str(e)})"
