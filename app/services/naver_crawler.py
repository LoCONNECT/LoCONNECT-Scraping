from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from typing import List, Dict

# 네이버

def _get_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,1024")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def get_menu_from_naver(keyword: str) -> List[Dict]:
    driver = _get_driver()
    try:
        # 검색 페이지 진입
        driver.get(f"https://map.naver.com/p/search/{keyword}")
        time.sleep(3)

        # iframe URL 추출
        iframe = driver.find_element("css selector", "iframe#entryIframe")
        iframe_url = iframe.get_attribute("src")

        if not iframe_url:
            print("[ERROR] iframe URL 추출 실패")
            return []

        # iframe 실제 페이지 이동
        driver.get(iframe_url)
        time.sleep(2)

        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")
        menu_items: List[Dict] = []

        for li in soup.select(".place_section_content .E2jtL"):
            name_tag = li.select_one(".lPzHi")
            name = name_tag.get_text(strip=True) if name_tag else ""
            if name:
                menu_items.append({"name": name})

        return menu_items

    except Exception as e:
        print(f"[ERROR] 메뉴 크롤링 실패: {e}")
        return []

    finally:
        driver.quit()
