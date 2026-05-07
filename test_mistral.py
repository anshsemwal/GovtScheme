import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

url = "https://api.mistral.ai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

print(f"Testing Mistral API Key: {api_key}")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Models found:")
        print([m['id'] for m in response.json()['data'][:5]])
    else:
        print(f"Failed error response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
