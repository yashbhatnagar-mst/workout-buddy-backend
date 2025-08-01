from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.utils.groq import get_groq_chat_response
import re

router = APIRouter()

# Pydantic schema for request validation
class ChatRequest(BaseModel):
    message: str

# Convert markdown to HTML
def format_response(text: str) -> str:
    if not text:
        return "⚠️ No response received from assistant."
    
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = text.replace("\n", "<br>")
    text = re.sub(r"(?m)^\* ", "• ", text)
    return text

@router.post("/chat")
async def chat(message: ChatRequest, request: Request):
    user_message = message.message.strip()

    if not user_message:
        return {"response": "⚠️ Please enter a message."}

    # Strict check: only allow fitness-related messages

    response = get_groq_chat_response(user_message)
    formatted_response = format_response(response)
    return {"response": formatted_response}
