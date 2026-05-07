import re

file_path = r'c:\Users\Md Zaid\Desktop\Major Project\GovtScheme-main\app\knowledge_base\schemes_data.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'https://pmjdy.gov.in/': 'https://www.pmjdy.gov.in/',
    'https://wcd.nic.in/bbbp-schemes': 'https://wcd.nic.in/',
    'https://pmmvy.nic.in/': 'https://pmmvy.wcd.gov.in/',
    'https://poshan.gov.in/': 'https://poshanabhiyaan.gov.in/',
    'https://civilaviation.gov.in/rcs-udaan': 'https://www.aai.aero/en/rcsudan/rcs-udan-1',
    'https://mnre.gov.in/solar/pm-kusum/': 'https://pmkusum.mnre.gov.in/',
    'https://serviceplus.gov.in/': 'https://serviceonline.gov.in/',
    '[serviceplus.gov.in]': '[serviceonline.gov.in]'
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
