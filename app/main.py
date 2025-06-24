import time
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse
import requests

# 초기 클론 pip install poetry
# poetry install === npm i (팀원 각자 가상환경 만들어야 함)
# 서버 키는 명령어 poetry run uvicorn app.main:app --reload (= FastAPI 실행)

app = FastAPI()

BASE_URL = "https://www.diningcode.com"

# def get_restaurants(keyword: str):
#     search_url = f"{BASE_URL}/list.dc?query={urllib.parse.quote(keyword)}"
#     headers = {
#         "User-Agent": (
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#             "AppleWebKit/537.36 (KHTML, like Gecko) "
#             "Chrome/124.0.0.0 Safari/537.36"
#         )
#     }
#     print(f"검색 URL: {search_url}")
#     res = requests.get(search_url, headers=headers)
#     print(f"HTTP Status: {res.status_code}")
#     res.raise_for_status()
#     print("HTML 내용 일부:", res.text[:500])  # 처음 500자만 미리보기

#     with open("debug.html", "w", encoding="utf-8") as f:
#         f.write(res.text)
#     print("debug.html 저장 완료")

#     soup = BeautifulSoup(res.text, "html.parser")
#     restaurants = []
#     for idx, a_tag in enumerate(soup.select("a.PoiBlock")):
#         href = a_tag.get("href", "")
#         print(f"{idx}번째 a.PoiBlock href: {href}")
#         if "/profile.php?rid=" not in href:
#             continue
#         rid = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("rid", [None])[0]
#         name_tag = a_tag.select_one("h2")
#         name = name_tag.get_text(strip=True) if name_tag else "이름 없음"
#         print(f"식당 발견: name={name}, rid={rid}")
#         restaurants.append({"name": name, "rid": rid})

#     print(f"총 {len(restaurants)}개 식당 탐색됨")
#     return restaurants

# def get_menu_from_profile(rid: str):
#     url = f"{BASE_URL}/profile.php?rid={rid}"
#     print(f"[메뉴 크롤링 시도: {url}")

#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     driver = webdriver.Chrome(options=options)

#     try:
#         driver.get(url)
#         print("Selenium 페이지 로드 완료")
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "ul.Restaurant_MenuList"))
#         )

#         name = driver.find_element(By.CSS_SELECTOR, "h2").text.strip()
#         menu_items = driver.find_elements(By.CSS_SELECTOR, "ul.Restaurant_MenuList li")
#         menus = []

#         for idx, item in enumerate(menu_items):
#             try:
#                 menu_name = item.find_element(By.CSS_SELECTOR, "span.Restaurant_Menu").text.strip()
#             except Exception as e:
#                 menu_name = ""
#                 print(f"{idx}번째 메뉴명 추출 실패: {e}")
#             try:
#                 menu_price = item.find_element(By.CSS_SELECTOR, "p.Restaurant_MenuPrice").text.strip()
#             except Exception as e:
#                 menu_price = ""
#                 print(f"{idx}번째 메뉴가격 추출 실패: {e}")
#             if menu_name or menu_price:
#                 menus.append(f"{menu_name} {menu_price}".strip())

#         print(f"메뉴 개수: {len(menus)}")
#         return name, "\n".join(menus) if menus else "메뉴 정보 없음"

#     except Exception as e:
#         print(f"메뉴 크롤링 실패: {e}")
#         return "에러", f"메뉴 크롤링 실패: {str(e)}"

#     finally:
#         driver.quit()
#         print(" Selenium 드라이버 종료")

# @app.get("/scrape")
# def scrape_menus(keyword: str = Query(..., description="검색할 지역명 또는 키워드")):
#     print(f"/scrape 진입, keyword={keyword}")
#     restaurants = get_restaurants(keyword)
#     result_lines = []

#     for r in restaurants:
#         if not r["rid"]:
#             print(f"rid 없음, 건너뜀: {r}")
#             continue
#         print(f"메뉴 크롤링 시작: {r['name']} ({r['rid']})")
#         name, menus = get_menu_from_profile(r["rid"])
#         print(f"메뉴 크롤링 완료: {name}")
#         result_lines.append(f"[{name}]\n{menus}\n")

#     with open("menus.txt", "w", encoding="utf-8") as f:
#         f.write("\n".join(result_lines))
#     print(f"menus.txt 저장 완료 ({len(result_lines)}개 식당)")

#     return {"msg": f"{len(result_lines)}개 식당의 메뉴 정보를 menus.txt에 저장했습니다."}


# 키워드 검색 함수
def get_restaurants_via_api(keyword: str):
    print("[INFO] API 방식으로 식당 목록 수집 시작")
    page = 1
    size = 20
    result = []
    MAX_PAGE = 200  # 🔒 여기에 최대 페이지 제한 추가!

    while page <= MAX_PAGE:
        url = "https://im.diningcode.com/API/isearch/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.diningcode.com",
            "Referer": "https://www.diningcode.com/"
        }
        data = {
            "query": keyword,
            "page": str(page),
            "size": str(size),
            "order": "r_score",
            "rn_search_flag": "on",
            "search_type": "poi_search",
        }

        res = requests.post(url, headers=headers, data=data)
        if res.status_code != 200:
            print(f"[ERROR] 요청 실패: {res.status_code}")
            break

        json_data = res.json()
        items = json_data.get("result_data", {}).get("poi_section", {}).get("list", [])
        print(f"[INFO] {page}페이지: {len(items)}개 수집")

        if not items:
            print("[INFO] 더 이상 데이터 없음, 수집 종료")
            break

        for item in items:
            result.append({
                "name": item.get("nm"),
                "addr": item.get("addr"),
                "cate": item.get("cate"),
                "score": item.get("score"),
                "v_rid": item.get("v_rid"),
            })

        page += 1

    print(f"[INFO] 총 {len(result)}개 식당 수집 완료 (최대 {MAX_PAGE} 페이지)")
    return result


@app.get("/restaurants")
def get_restaurants(keyword: str = Query(..., description="검색할 키워드")):
    try:
        return get_restaurants_via_api(keyword)
    except Exception as e:
        print(f"[ERROR] 크롤링 중 오류: {e}")
        return JSONResponse(status_code=500, content={"message": "크롤링 실패", "detail": str(e)})