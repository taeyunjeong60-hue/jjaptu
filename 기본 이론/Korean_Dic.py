import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
Userinput=input("단어 입력:")
apikey=os.getenv("korean_dic_api_key")
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