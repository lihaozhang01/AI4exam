# backend/tests/test_api.py

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_streaming_endpoint():
    """
    Tests the full flow:
    1. Create a test entry to get a test_id.
    2. Use the test_id to call the streaming generation endpoint.
    """
    print("--- Step 1: Creating test entry ---")
    create_test_config = {
        "description": "Test description for AI history",
        "question_config": [
            {"type": "multiple_choice", "count": 1},
            {"type": "short_answer", "count": 1}
        ],
        "difficulty": "easy"
    }
    create_test_files = {
        'config_json': (None, json.dumps(create_test_config)),
        'source_text': (None, 'This is a test source text about the history of AI.')
    }

    try:
        create_response = requests.post(f"{BASE_URL}/tests", files=create_test_files)
        create_response.raise_for_status()  # Raise an exception for bad status codes
        response_data = create_response.json()
        test_id = response_data.get("test_id")
        if not test_id:
            print("Error: 'test_id' not found in response:", response_data)
            return
        print(f"Successfully created test. Test ID: {test_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error creating test entry: {e}")
        return

    print("--- Step 2: Calling streaming endpoint ---")
    headers = {
        "X-Provider": "siliconflow",
        "X-Api-Key": "sk-ncqefslgsteweydggzsohtuuvosfsgpqqogsrjwybsvofevq",  # <--- IMPORTANT: Replace with your actual key
        "X-Generation-Model": "Qwen/Qwen2-7B-Instruct", # Or any other valid model
        "Accept": "text/event-stream"
    }

    try:
        stream_response = requests.get(
            f"{BASE_URL}/generate-stream-test/{test_id}",
            headers=headers,
            stream=True
        )
        stream_response.raise_for_status()

        print("--- Streaming Response ---")
        for chunk in stream_response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                print(chunk, end='')
        print("\n--- End of Stream ---")

    except requests.exceptions.RequestException as e:
        print(f"Error calling streaming endpoint: {e}")
        if e.response is not None:
            print("Response Body:", e.response.text)

if __name__ == "__main__":
    test_streaming_endpoint()