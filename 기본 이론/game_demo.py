import requests
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()
korean_con=["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
korean_gat=["ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅒ", "ㅔ", "ㅖ", "ㅘ", "ㅙ", "ㅚ", "ㅝ", "ㅞ", "ㅟ", "ㅢ"]

Userinput=input("""
자음:{}
                    
단어 입력:
                """)
apikey= os.getenv("korean_dic_api_key")
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