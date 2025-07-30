import requests
import json
import urllib.parse

# Import the prompt from the backend prompts module
# This assumes the test is run from a path where this import is valid
from backend.prompts import GENERATE_STREAMABLE_TEST_PROMPT

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
STREAM_ENDPOINT = f"{BASE_URL}/generate-stream-test"

# --- Test Payload ---
# This is the data we'll send to the API
TEST_PAYLOAD = {
    "knowledge_content": """
    Python 循环

    Python 中有两种主要的循环类型：`for` 循环和 `while` 循环。

    1. **for 循环**: 用于遍历序列（如列表、元组、字典、集合或字符串）。
       - 语法: `for item in sequence:`
       - 示例: `for fruit in ["apple", "banana", "cherry"]:
                   print(fruit)`

    2. **while 循环**: 只要条件为真，就会一直执行代码块。
       - 语法: `while condition:`
       - 示例: `count = 0
                 while count < 5:
                     print(count)
                     count += 1`
    """,
    "config": {
        "description": "关于 'Python 循环' 的随堂测试",
        "question_config": [
            {
                "type": "multiple_choice",
                "count": 2
            },
            {
                "type": "essay",
                "count": 1
            }
        ],
        "difficulty": "中等"
    }
}

def run_streaming_test():
    """ 
    Runs the streaming test by sending a POST request to the API and 
    processing the server-sent events (SSE) stream.
    """
    # The prompt needs to be URL-encoded to be safely sent in a header.
    # We convert the entire prompt dictionary to a string, then encode it.
    system_prompt_text = GENERATE_STREAMABLE_TEST_PROMPT['system_prompt']
    encoded_prompt = urllib.parse.quote(system_prompt_text)

    headers = {
        "X-Api-Key": "AIzaSyAj8vi0OUr1xRM5GGt88FnmbqZ7P79-xDU",
        "X-Generation-Model": "gemini-1.5-flash",
        "X-Generation-Prompt": encoded_prompt,
    }

    # The API expects multipart/form-data. We only need to send the text and config.
    payload = {
        'source_text': (None, TEST_PAYLOAD['knowledge_content'], 'text/plain; charset=utf-8'),
        'config_json': (None, json.dumps(TEST_PAYLOAD['config']), 'application/json'),
    }

    print(f"🚀 Starting test: POST to {STREAM_ENDPOINT}")
    print("--- Headers ---")
    print(json.dumps(headers, indent=2))
    print("--- Payload (as multipart/form-data) ---")
    # Iterate over the payload to print its contents for debugging
    for key, value in payload.items():
        # value is a tuple (filename, content), we print the content part
        print(f"{key}: {value[1]}")
    print("-----------------\n")

    try:
        # `stream=True` is crucial for handling streaming responses
        # We send `files` instead of `data` because we are sending multipart/form-data
        with requests.post(STREAM_ENDPOINT, files=payload, headers=headers, stream=True, timeout=300) as response:

            # Check if the request was successful
            if response.status_code != 200:
                print(f"❌ Error: Received status code {response.status_code}")
                print("--- Response Body ---")
                print(response.text)
                print("---------------------")
                return

            print("✅ Connection successful. Waiting for stream data...\n")
            
            # Process the stream line by line to handle Server-Sent Events (SSE)
            print("--- Parsing SSE Stream ---")
            buffer = ""
            # Use iter_content to get raw chunks and handle decoding manually
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=False):
                if chunk:
                    # Decode chunk by chunk and process lines
                    decoded_chunk = chunk.decode('utf-8')
                    buffer += decoded_chunk

                    # Process complete lines from the buffer
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line.startswith('data: '):
                            data_segment = line[len('data: '):]
                            # Now, we process this segment with the existing logic.
                            # To avoid duplicating the logic, let's imagine a helper function.
                            # Try to parse the data segment as JSON and print it
                            try:
                                json_data = json.loads(data_segment)
                                # Pretty-print the JSON data
                                print(json.dumps(json_data, indent=2, ensure_ascii=False))
                            except json.JSONDecodeError:
                                # If it's not valid JSON, print it as is for debugging
                                print(f"[NON-JSON DATA] {data_segment}")

            # After the loop, process any remaining data in the buffer
            if buffer.strip().startswith('data: '):
                remainder_data = buffer.strip()[len('data: '):]
                try:
                    json_data = json.loads(remainder_data)
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(f"[NON-JSON REMAINDER] {remainder_data}")


            print("\n--- End of Stream ---")

    except requests.exceptions.RequestException as e:
        print(f"❌ CRITICAL ERROR: Could not connect to the server.")
        print(f"   Please ensure the FastAPI server is running on {BASE_URL}")
        print(f"   Error details: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    run_streaming_test()