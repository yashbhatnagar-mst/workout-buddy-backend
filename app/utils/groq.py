from openai import OpenAI
from app.config.settings import settings

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=settings.GROQ_API_KEY
)

def get_groq_response(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You're a helpful fitness assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
def get_groq_chat_response(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful and expert fitness assistant. "
                        "Only respond to questions strictly related to fitness, health, workouts, nutrition, or diet. "
                        "If the question is unrelated to fitness, politely refuse to answer and remind the user "
                        "that you are only trained to help with fitness-related topics."
                    )
                },
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
