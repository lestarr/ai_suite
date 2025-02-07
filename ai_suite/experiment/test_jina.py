import requests
import urllib.parse
from ai_suite.ie.utils.utils import clean_markdown
query = "Atomico venture capital website"
encoded_query = urllib.parse.quote(query)
url = f"https://s.jina.ai/{encoded_query}"
headers = {
    "Authorization": "Bearer jina_b029d15812ac4b3d95676264dfb9810cG0P5sDzIlcPwnUHbRMq6oMDbz_Rv",
    "X-Return-Format": "markdown"
}

headers = {
    "X-Return-Format": "markdown"
}

headers = {
    "X-Return-Format": "markdown",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Cookie": 'session-id=42-1174173-5861509; session-token=PUeiuw75VzQnE2BzSSb/vQQTpvvAB4lQbuYHEMW1i71f//qEy11Anvh8lAHEmxGGsfv/usw13ffYrF0xgDZnn72YIktwewbQqOCTb23qmxhTnoR9uITeIAJK+i7vyg/44WeHD5S7/oLeUJlq82Ll/medCRMh01Xn7fOYumPxyto63d3UXPlTbYm2MIjl3D5/q73DyEgSVOVZnF30fP4kzBpvqZ2hrNLi43PfYAvC3/eTMzhzhk+fwXEsK473Xr49PNCqAYwlhf49mV7fY39y2sKiDOcCWedVAYEgZkMtLWA6FWuk3VBns5Vv/Z3OjqqX8awdAcHB9gakgjtpA6zHqcoRbpTxt5HjBg1TMjSBzUfU+0SivJtpkNldcPXSZ3Sr1df/1ganrTdSQsFKIUmPxdK913HyPsiA8sX7hSKsK7wZujDynHyGkw==; i18n-prefs=USD;',
    "Referer": "https://www.amazon.com/"
}

headers = {
    "X-Return-Format": "markdown",
    'X-Set-Cookie': 'session-id=42-1174173-5861509, session-token=PUeiuw75VzQnE2BzSSb/vQQTpvvAB4lQbuYHEMW1i71f//qEy11Anvh8lAHEmxGGsfv/usw13ffYrF0xgDZnn72YIktwewbQqOCTb23qmxhTnoR9uITeIAJK+i7vyg/44WeHD5S7/oLeUJlq82Ll/medCRMh01Xn7fOYumPxyto63d3UXPlTbYm2MIjl3D5/q73DyEgSVOVZnF30fP4kzBpvqZ2hrNLi43PfYAvC3/eTMzhzhk+fwXEsK473Xr49PNCqAYwlhf49mV7fY39y2sKiDOcCWedVAYEgZkMtLWA6FWuk3VBns5Vv/Z3OjqqX8awdAcHB9gakgjtpA6zHqcoRbpTxt5HjBg1TMjSBzUfU+0SivJtpkNldcPXSZ3Sr1df/1ganrTdSQsFKIUmPxdK913HyPsiA8sX7hSKsK7wZujDynHyGkw==; domain=amazon.com'
}

#response = requests.get(url, headers=headers)
# READER API
url = "https://atomico.com/"
#url = "https://www.herox.com/crowdsourcing-projects"
url = "https://www.amazon.com/your-orders/orders?timeFilter=year-2024&startIndex=0&ref_=ppx_yo2ov_dt_b_pagination_1_1"
url = f"https://r.jina.ai/{url}"
response = requests.get(url, headers=headers)
# Print raw response content
text = response.text
clean_text = clean_markdown(text)

print("Raw Response Content:\n", clean_text)
#redirect into file
with open("test_jina.txt", "w") as file:
    file.write(clean_text)
print()
print()
print()
print(response)
