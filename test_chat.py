import requests
import json

url = "http://127.0.0.1:8001/api/chat"
payload = {
    "message": "financial assistance for low income families",
    "session_id": "test_session",
    "context": {
        "age": 30,
        "income": 200000,
        "location": "Delhi"
    }
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
