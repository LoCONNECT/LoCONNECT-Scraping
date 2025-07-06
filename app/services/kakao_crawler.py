import os
import re
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

load_dotenv()
KAKAO_REST_KEY = os.getenv("KAKAO_REST_KEY")


def extract_area(addr: str) -> str:
    """주소에서 '성남시 분당구' 식 지역명 추출"""
    m = re.search(r"[가-힣]+시\s+[가-힣]+구", addr)
    return m.group() if m else addr.split()[0]


def get_kakao_place_id(name: str, addr: str) -> Optional[int]:
    """가게 이름 + 주소 일부(구 단위)로 place_id 검색"""
    area = extract_area(addr)
    query = f"{name} {area}"

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"query": query, "size": 1}
    r = requests.get(
        "https://dapi.kakao.com/v2/local/search/keyword.json",
        headers=headers,
        params=params,
        timeout=10,
    )

    if r.status_code != 200:
        print(f"[ERROR] Kakao API 응답 코드 {r.status_code}")
        return None

    docs = r.json().get("documents", [])
    if not docs:
        print(f"[MISS] {query} → 검색 결과 없음")
        return None

    return int(docs[0]["id"])


def get_menu_from_kakao(place_id: int) -> List[Dict]:
    """Selenium으로 Kakao 메뉴 스크래핑 (메뉴 탭 클릭 포함)"""
    url = f"https://place.map.kakao.com/{place_id}#menuInfo"  # 메뉴탭 직접 이동

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(url)

        # 메뉴 항목 로드 대기 (.tit_item 있는지 확인)
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.list_goods > li")
                )
            )
        except TimeoutException:
            raise ValueError("메뉴 리스트가 로딩되지 않음 (Timeout)")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("ul.list_goods > li")
        menus: List[Dict] = []

        for li in items:
            name_tag = li.select_one(".tit_item")
            price_tag = li.select_one(".desc_item")
            if name_tag:
                menus.append(
                    {
                        "name": name_tag.get_text(strip=True),
                        "price": price_tag.get_text(strip=True) if price_tag else None,
                        "img": None,
                    }
                )

        if not menus:
            raise ValueError("메뉴 태그는 있지만 항목이 0개")

        return menus

    except Exception as e:
        print(
            f"[ERROR] Kakao 메뉴 수집 실패: place_id={place_id} "
            f"→ {type(e).__name__}: {e}"
        )
        raise

    finally:
        driver.quit()


__all__ = ["get_kakao_place_id", "get_menu_from_kakao"]
