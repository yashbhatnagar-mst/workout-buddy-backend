# app/utils/gemini.py
import google.generativeai as genai  # type: ignore
from app.api.routes.api_key import get_api_key

# Global variable to store the configured model
model = None

async def configure_gemini_model():
    """
    Configures the Gemini API and initializes the model.
    This function should be called once during application startup.
    """
    global model
    try:
        response = await get_api_key()
        api_key = response["data"]["apiKey"]
        print(f"Using GEMINI_API_KEY: {api_key}")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please ensure it's provided by get_api_key.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
        print("Gemini model configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        # Depending on your application, you might want to raise the exception
        # or handle it differently to prevent the app from starting with a misconfigured API.

async def generate_gemini_response(prompt: str) -> str:
    """Generates content from Gemini API based on a prompt asynchronously."""
    if model is None:
        return "Error: Gemini model not initialized. Please ensure configure_gemini_model runs on startup."
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred during Gemini response generation: {e}")
        return "Error: Could not generate content."

# No asyncio.run() here
# The main() and if __name__ == "__main__": block are not needed in this file
# if you're using this module as part of a larger FastAPI application.