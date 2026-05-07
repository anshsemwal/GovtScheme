import requests

test_urls = [
    "https://pmkisan.gov.in/",
    "https://pmay-urban.gov.in/",
    "https://pmuy.gov.in/",
    "https://udyamimitra.in/",
    "https://pmjay.gov.in/",
    "https://pmjdy.gov.in/",
    "https://wcd.nic.in/bbbp-schemes",
    "https://www.indiapost.gov.in/",
    "https://jansuraksha.gov.in/",
    "https://www.skillindiadigital.gov.in/",
    "https://swachhbharatmission.gov.in/",
    "https://nrega.nic.in/",
    "https://pmsvanidhi.mohua.gov.in/",
    "https://pmksy.gov.in/",
    "https://pmfby.gov.in/",
    "https://pmmvy.nic.in/",
    "https://www.standupmitra.in/",
    "https://poshan.gov.in/",
    "https://civilaviation.gov.in/rcs-udaan",
    "https://saubhagya.gov.in/",
    "https://janaushadhi.gov.in/",
    "https://samadhaan.msme.gov.in/",
    "https://socialjustice.gov.in/schemes/71",
    "https://mnre.gov.in/solar/pm-kusum/",
    "https://nrlm.gov.in/",
    "https://pmvishwakarma.gov.in/",
    "https://serviceplus.gov.in/"
]

headers = {'User-Agent': 'Mozilla/5.0'}

for url in test_urls:
    try:
        response = requests.get(url, timeout=5, headers=headers)
        print(f"{url}: {response.status_code}")
    except Exception as e:
        print(f"{url}: ERROR ({e})")
