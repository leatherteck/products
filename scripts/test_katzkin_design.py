import requests
from bs4 import BeautifulSoup

# Test with 2020 Dodge Challenger GT
year = "2020"
make = "DODGE"
model = "CHALLENGER"
trim = "GT"

url = f"http://www.katzkinvis.com/interiorselector/getExtData/katzkinGetVISCodes_mobile.php?make={make}&model={model}&year={year}&trim={trim}"

print(f"Testing: {year} {make} {model} {trim}")
print(f"URL: {url}\n")

response = requests.get(url)

if response.status_code == 200:
    print("Response received!")
    print("\n=== RAW HTML ===")
    print(response.text[:2000])  # Print first 2000 chars
    print("\n...")

    # Save full response to file for inspection
    with open('katzkin_design_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nFull response saved to: katzkin_design_response.html")
else:
    print(f"Error: {response.status_code}")
