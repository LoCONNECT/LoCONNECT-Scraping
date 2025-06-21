from fastapi import FastAPI, Query
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse
import requests

app = FastAPI()

BASE_URL = "https://www.diningcode.com"

#  1. 검색어로 식당 목록 수집
def get_restaurants(keyword: str):
    search_url = f"{BASE_URL}/list.dc?query={urllib.parse.quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(search_url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    restaurants = []
    for a_tag in soup.select("a.PoiBlock"):
        href = a_tag.get("href", "")
        if "/profile.php?rid=" not in href:
            continue

        rid = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("rid", [None])[0]
        name_tag = a_tag.select_one("h2")
        name = name_tag.get_text(strip=True) if name_tag else "이름 없음"
        restaurants.append({"name": name, "rid": rid})

    return restaurants


# 2. Selenium으로 메뉴 정보 수집
def get_menu_from_profile(rid: str):
    url = f"{BASE_URL}/profile.php?rid={rid}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

       
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.Restaurant_MenuList"))
        )

        name = driver.find_element(By.CSS_SELECTOR, "h2").text.strip()
        menu_items = driver.find_elements(By.CSS_SELECTOR, "ul.Restaurant_MenuList li")
        menus = []

        for item in menu_items:
            try:
                menu_name = item.find_element(By.CSS_SELECTOR, "span.Restaurant_Menu").text.strip()
            except:
                menu_name = ""
            try:
                menu_price = item.find_element(By.CSS_SELECTOR, "p.Restaurant_MenuPrice").text.strip()
            except:
                menu_price = ""
            if menu_name or menu_price:
                menus.append(f"{menu_name} {menu_price}".strip())

        return name, "\n".join(menus) if menus else "메뉴 정보 없음"

    except Exception as e:
        return "에러", f"메뉴 크롤링 실패: {str(e)}"

    finally:
        driver.quit()


#  3. FastAPI 엔드포인트
@app.get("/scrape")
def scrape_menus(keyword: str = Query(..., description="검색할 지역명 또는 키워드")):
    restaurants = get_restaurants(keyword)
    result_lines = []

    for r in restaurants:
        if not r["rid"]:
            continue
        name, menus = get_menu_from_profile(r["rid"])
        result_lines.append(f"[{name}]\n{menus}\n")

    with open("menus.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))

    return {"msg": f"{len(result_lines)}개 식당의 메뉴 정보를 menus.txt에 저장했습니다."}
