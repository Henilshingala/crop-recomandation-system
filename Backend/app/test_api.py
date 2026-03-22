import requests
import json

# Test with proper UTF-8 encoding
url = "http://127.0.0.1:8000/chat/"
data = {
    "question": "नमस्कार",
    "language": "gu"
}

headers = {
    "Content-Type": "application/json; charset=utf-8"
}

response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
