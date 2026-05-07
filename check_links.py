import re
import requests
from concurrent.futures import ThreadPoolExecutor

def extract_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Improved regex to find [label](url) where url is inside ()
    matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
    return matches

def check_link(name, url):
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        status = response.status_code
        if status == 200:
            return None # Working
        return (name, url, status)
    except Exception as e:
        return (name, url, str(e))

def main():
    file_path = r'c:\Users\Md Zaid\Desktop\Major Project\GovtScheme-main\app\knowledge_base\schemes_data.py'
    links = extract_links(file_path)
    print(f"Found {len(links)} links. Checking...")
    
    broken_links = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda p: check_link(*p), links)
        for res in results:
            if res:
                broken_links.append(res)
    
    if not broken_links:
        print("All links are working!")
    else:
        print(f"Found {len(broken_links)} broken links:")
        for name, url, error in broken_links:
            print(f" - {name}: {url} (Error: {error})")

if __name__ == "__main__":
    main()
