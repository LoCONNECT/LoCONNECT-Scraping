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

load_dotenv()
KAKAO_REST_KEY = os.getenv("KAKAO_REST_KEY")


def extract_area(addr: str) -> str:
    """주소에서 '성남시 분당구' 식 지역명 추출"""
    m = re.search(r"[가-힣]+시\s+[가-힣]+구", addr)
    return m.group() if m else addr.split()[0]


def get_menu_from_kakao(place_id: int) -> List[Dict]:
    """Selenium으로 Kakao 메뉴 스크래핑"""
    url = f"https://place.map.kakao.com/{place_id}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # 요소 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".menu_box .list_menu li"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        menu_items = soup.select(".menu_box .list_menu li")
        menus = []

        for item in menu_items:
            name_el = item.select_one(".loss_word")
            price_el = item.select_one(".price_menu")
            if name_el:
                menus.append({
                    "name": name_el.text.strip(),
                    "price": price_el.text.strip() if price_el else None,
                    "img": None
                })

        if not menus:
            print(f"[WARN] 메뉴 태그는 있는데 메뉴 없음: place_id={place_id}")
            raise ValueError(f"메뉴 없음")

        return menus

    except Exception as e:
        print(f"[ERROR] Kakao 메뉴 수집 실패: place_id={place_id} → {type(e).__name__}: {e}")
        raise

    finally:
        driver.quit()


__all__ = ["get_kakao_place_id", "get_menu_from_kakao"]
