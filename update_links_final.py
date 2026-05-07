import re

file_path = r'c:\Users\Md Zaid\Desktop\Major Project\GovtScheme-main\app\knowledge_base\schemes_data.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'https://wcd.nic.in/': 'https://wcd.gov.in/',
    'wcd.nic.in': 'wcd.gov.in' # to update labels too
}

new_content = content
for old, new in replacements.items():
    new_content = new_content.replace(old, new)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Sucessfully updated scheme links in database.")
else:
    print("No changes needed or links already updated.")
