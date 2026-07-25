import requests
import json

Userinput=input("단어 입력:")
apikey="8392370E3F14C500277E590A1F542B46"
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