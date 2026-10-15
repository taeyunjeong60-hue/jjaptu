import requests
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()
korean_con=["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
korean_gat=["ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅒ", "ㅔ", "ㅖ", "ㅘ", "ㅙ", "ㅚ", "ㅝ", "ㅞ", "ㅟ", "ㅢ"]
random_con=str(random.choice(korean_con))
random_gat=str(random.choice(korean_gat))


Userinput=input(f"""
자음:{random_con} 
모음:{random_gat}
                    
단어 입력:""")
apikey='apikey'
print(apikey)
url = "https://stdict.korean.go.kr/api/search.do"

params = {
    "key" : apikey, 
    "q" : Userinput,
    "req_type" : "json",
    "num":10
}

response = requests.get(url,params=params)

data=(json.loads(response.text) if response.text!="" else 0)
print((params["q"] if data!=0 else "no found"))