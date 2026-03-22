import requests
import json
import os

BASE_URL = "http://localhost:8000/api"

def test_assistant():
    print("Testing AI Assistant Non-Streaming...")
    data = {
        "message": "你好，请给我写一个关于Python的简单介绍。"
    }
    r = requests.post(f"{BASE_URL}/assistant/", json=data)
    print("Status:", r.status_code)
    if r.status_code == 200:
        print("Response:", r.json())
    else:
        print("Error:", r.text)

    print("\nTesting AI Assistant Streaming...")
    r = requests.post(f"{BASE_URL}/assistant/stream", json=data, stream=True)
    print("Status:", r.status_code)
    if r.status_code == 200:
        print("Streaming Output:")
        # We use simple iter_lines for SSE/chunked
        for line in r.iter_lines():
            if line:
                print(line.decode('utf-8'))
    else:
        print("Error:", r.text)

if __name__ == "__main__":
    test_assistant()
