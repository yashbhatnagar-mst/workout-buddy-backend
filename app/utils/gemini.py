import google.generativeai as genai  # type: ignore
from app.api.routes.api_key import get_api_key

# Global variable to store the configured Gemini model
model = None

async def configure_gemini_model():
    """
    Configures the Gemini API and initializes the model.
    This function should be called once during application startup.
    """
    global model
    try:
        response = await get_api_key()
        # print(response)
        # Validate the structure of the response
        if not response or "data" not in response or "apiKey" not in response["data"]:
            raise ValueError("Invalid API key response format or missing API key.")

        api_key = response["data"]["apiKey"]
        print(f"Using GEMINI_API_KEY: {api_key}")

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-pro")
        print("✅ Gemini model configured successfully.")
        
    except Exception as e:
        print(f"❌ Error configuring Gemini: {e}")

async def generate_gemini_response(prompt: str) -> str:
    """
    Generates content from Gemini API based on a prompt asynchronously.
    """
    if model is None:
        return "Error: Gemini model not initialized. Please ensure configure_gemini_model runs on startup."
    
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"❌ An error occurred during Gemini response generation: {e}")
        return "Error: Could not generate content."
