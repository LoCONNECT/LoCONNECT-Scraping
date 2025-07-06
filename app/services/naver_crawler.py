import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def search_naver_place_id(query: str) -> Optional[str]:
    """네이버 지역 검색 API로 place_id 추출"""
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": query}
    url = "https://openapi.naver.com/v1/search/local.json"

    r = requests.get(url, headers=headers, params=params, timeout=5)
    if r.status_code != 200:
        print(f"[ERROR] Naver 지역 검색 실패: {r.status_code}")
        return None

    items = r.json().get("items", [])
    if not items:
        return None

    # blog.naver.com/abcd/place/1234 이런 식의 url에서 1234가 place_id
    return items[0]["link"]


def get_menu_from_naver(place_link: str) -> List[Dict]:
    """네이버 플레이스 HTML 파싱해서 메뉴 추출"""
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(place_link, headers=headers, timeout=5)

    if r.status_code != 200:
        raise ValueError(f"[ERROR] 네이버 메뉴 HTML 요청 실패: {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    menu_elems = soup.select("ul.place_section_content span.Fc1rA")  # 메뉴명
    price_elems = soup.select("ul.place_section_content span.Yrbzj")  # 가격

    menus = []
    for name, price in zip(menu_elems, price_elems):
        menus.append({
            "name": name.get_text(strip=True),
            "price": price.get_text(strip=True),
            "img": None
        })

    return menus
