
import requests
import json

def test_chat_links():
    url = "http://127.0.0.1:8001/api/chat"
    payload = {
        "message": "Give me info on PM Kisan and show me the application link",
        "session_id": "test-session-123"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data['response']}")
        
        # Check if markdown link is present
        if "http" in data['response'] and "[" in data['response'] and "]" in data['response']:
            print("\nSUCCESS: Found markdown links in response!")
        else:
            print("\nFAILURE: No markdown links found in response.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat_links()
