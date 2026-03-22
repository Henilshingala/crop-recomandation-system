import requests
import json

def test_chat(question, language):
    url = "http://127.0.0.1:8000/chat/"
    data = {
        "question": question,
        "language": language
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    print(f"Question: {question} (Language: {language})")
    print(f"Matched: {result['matched']}, Score: {result['score']}")
    print(f"Response Language: {result.get('language_used', 'N/A')}")
    print(f"Answer: {result['answer'][:100]}...")
    print("-" * 50)

# Test cases
print("Testing language selection functionality:")
print("=" * 50)

# Test 1: Hindi input, Gujarati response
test_chat("नमस्कार", "gu")

# Test 2: Hindi input, Hindi response  
test_chat("नमस्कार", "hi")

# Test 3: Hindi input, English response
test_chat("नमस्कार", "en")

# Test 4: English input, Gujarati response
test_chat("hi", "gu")
