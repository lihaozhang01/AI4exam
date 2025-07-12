import asyncio
import google.generativeai as genai
import os

async def main():
    """Tests the Google AI API key and connectivity."""
    try:
        # It's recommended to set the API key as an environment variable
        # For this test, we'll use the one provided.
        api_key = "AIzaSyCoG7xuzfPYVgbxSni6FPTC1YiV48UTi3w"
        genai.configure(api_key=api_key)

        print("Configured Google AI. Creating model...")
        model = genai.GenerativeModel('gemini-2.5-flash')

        print("Sending a test prompt to Google AI...")
        response = await model.generate_content_async("Hello, world!")

        print("Successfully received response from Google AI:")
        print(response.text)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())