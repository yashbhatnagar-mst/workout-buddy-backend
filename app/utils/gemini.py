import os
import google.generativeai as genai # type: ignore
from dotenv import load_dotenv
import asyncio 

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

async def generate_gemini_response(prompt: str) -> str:
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error: Could not generate content."

async def main():
    test_prompt = "Explain how AI works in a few words."
    response_text = await generate_gemini_response(test_prompt)
    print(response_text)

if __name__ == "__main__":
    asyncio.run(main())