import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def search_naver_place_id(query: str) -> Optional[str]:
    """
    네이버 지역 검색 API로 장소 링크 추출
    """
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": query}
    url = "https://openapi.naver.com/v1/search/local.json"

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Naver API 요청 실패 → {type(e).__name__}: {e}")
        return None

    items = res.json().get("items", [])
    if not items:
        print(f"[MISS] '{query}'에 대한 검색 결과 없음")
        return None

    return items[0].get("link")


def get_menu_from_naver(place_link: str) -> List[Dict]:
    """
    네이버 플레이스 HTML 파싱해서 메뉴 추출
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(place_link, headers=headers, timeout=5)
        res.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"[ERROR] 네이버 HTML 요청 실패: {type(e).__name__}: {e}")

    return _parse_menu_from_html(res.text)


def _parse_menu_from_html(html: str) -> List[Dict]:
    """
    HTML에서 메뉴명과 가격을 파싱
    """
    soup = BeautifulSoup(html, "html.parser")

    # 변동 가능한 클래스명 대신 구조적으로 접근
    menu_names = soup.select("ul.place_section_content span")
    prices = soup.select("ul.place_section_content span")

    # 필터링 조건: 메뉴명과 가격은 클래스 또는 텍스트 패턴으로 구분 가능
    name_list = [el.get_text(strip=True) for el in menu_names if el.get("class") and "Fc1rA" in el.get("class")]
    price_list = [el.get_text(strip=True) for el in prices if el.get("class") and "Yrbzj" in el.get("class")]

    menus = []
    for name, price in zip(name_list, price_list):
        menus.append({
            "name": name,
            "price": price,
            "img": None
        })

    if not menus:
        print("[WARN] 메뉴 파싱 결과가 비어 있음")

    return menus
