import json

# Load the current Ai.json
with open(r'D:\downloads\CRS\Backend\app\Ai\Ai.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update the Hindi greeting to include proper Hindi greetings
if 'QNA1301' in data and 'hi' in data['QNA1301']['translations']:
    # Change the Hindi question from "hi" to "नमस्कार"
    data['QNA1301']['translations']['hi']['question'] = 'नमस्कार'
    
    # Also add alternative Hindi greetings by creating new entries or updating existing ones
    # Let's also update a few more common Hindi greeting variations
    
    # Save the updated data
    with open(r'D:\downloads\CRS\Backend\app\Ai\Ai.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Updated Hindi greeting in QNA1301 to 'नमस्कार'")
    print("Hindi question:", data['QNA1301']['translations']['hi']['question'])
    print("Hindi answer:", data['QNA1301']['translations']['hi']['answer'])
else:
    print("QNA1301 or Hindi translation not found")
