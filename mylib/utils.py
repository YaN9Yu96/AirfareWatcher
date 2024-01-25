import time
import random
import requests

def get_url(url: str):
    response = ""
    retry = 5
    for i in range(retry):
        try:
            response = requests.get(url, headers=get_user_agent(), timeout=10)
            break
        except:
            print(f"访问 {url} 失败, 重试 {i + 1}/{retry}")
            time.sleep(1)
    response.close()
    return response


def get_user_agent():
    return {"User-Agent": random.choice(user_agents)}


user_agents = ["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9"]
