import requests
from typing import List, Dict

# 카카오 아직 안해봄
def get_menu_from_kakao(place_id:int)->list[dict]:
    url = f"https://place.map.kakao.com/main/v/{place_id}"
    data = requests.get(url, timeout=10).json()
    return [
        {"name":m["menu"], "price":m.get("price"), "img":m.get("imgPath")}
        for m in data.get("menuInfo", [])
    ]