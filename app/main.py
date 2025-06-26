import os, time, logging, requests
from typing import List, Dict
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# pthon 3.13버전 설치
# 초기 클론 pip install poetry
# (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
# poetry install  === npm i (팀원 각자 가상환경 만들어야 함)
# 서버 키는 명령어 poetry run uvicorn app.main:app --reload (= FastAPI 실행)

app = FastAPI()
BASE_URL = "https://www.diningcode.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ───────────────────────────────────────────────
# 공통 ChromeDriver 생성기 ― 필요한 곳에서 호출해 사용 후 quit()
def create_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")     # ↔ "--headless=old" 테스트 가능
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--disable-gpu")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_opts,
    )

# ───────────────────────────────────────────────
# 식당 한 곳 메뉴를 DOM으로 끝까지 펼쳐 추출
def get_menu_items_by_dom(rid: str) -> List[Dict]:
    url = f"{BASE_URL}/profile.php?rid={rid}"
    log = logging.getLogger("menu")
    log.info(f"크롤링 시작: {url}")
    
    driver = create_driver(headless=True)
    menus: List[Dict] = []

    try:
        driver.get(url)
        click_count = 0
        MAX_CLICK = 5
        while click_count < MAX_CLICK:
            try:
                more_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-hidden"))
                )
                driver.execute_script("arguments[0].click();", more_btn)
                click_count += 1
                time.sleep(6)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                break  # 더보기 없거나 클릭 불가

        #  메뉴 리스트 등장 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.Restaurant_MenuList"))
        )

        #  BeautifulSoup 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for li in soup.select("ul.Restaurant_MenuList > li"):
            name_tag = li.select_one("strong.Restaurant_Menu")
            price_tag = li.select_one("span.Restaurant_MenuPrice")
            name = name_tag.get_text(strip=True) if name_tag else None
            if not name:
                continue
            price = price_tag.get_text(strip=True) if price_tag else None
            menus.append({"name": name, "price": price})

        log.info(f"메뉴 {len(menus)}개 추출 완료 (rid={rid})")
    except Exception as e:
        log.error(f"메뉴 크롤링 실패(rid={rid}): {e}")
    finally:
        driver.quit()

    return menus

# 키워드로 식당 목록 수집 (중복 페이지 감지 포함)
def get_restaurants(keyword: str) -> List[Dict]:
    logging.info("식당 목록 수집 시작")
    page, size = 1, 20
    seen_rids, result = set(), []
    MAX_REPEAT, repeated = 3, 0              # ← 페이지 중복 감지용

    while True:
        r = requests.post(
            "https://im.diningcode.com/API/isearch/",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": BASE_URL,
                "Referer": BASE_URL + "/",
            },
            data={
                "query": keyword,
                "page": str(page),
                "size": str(size),
                "order": "r_score",
                "rn_search_flag": "on",
                "search_type": "poi_search",
            },
            timeout=10,
        )
        if r.status_code != 200:
            logging.error(f"목록 API 오류: {r.status_code}")
            break

        items = (
            r.json()
            .get("result_data", {})
            .get("poi_section", {})
            .get("list", [])
        )
        if not items:
            break

        logging.info(f"{page}페이지: {len(items)}개")

        # 페이지 전체가 중복인지 확인
        page_rids = [it["v_rid"] for it in items]
        if all(r in seen_rids for r in page_rids):
            repeated += 1
            if repeated >= MAX_REPEAT:
                logging.info("반복 페이지 감지 → 종료")
                break
        else:
            repeated = 0  # 새로운 RID가 있으면 카운트 리셋

        # 결과 누적
        for it in items:
            rid = it["v_rid"]
            if rid in seen_rids:
                continue
            seen_rids.add(rid)
            result.append(
                {
                    "name": it.get("nm"),
                    "addr": it.get("addr"),
                    "cate": it.get("cate"),
                    "score": it.get("score"),
                    "v_rid": rid,
                }
            )
        page += 1

    logging.info(f"식당 {len(result)}곳 수집 완료: {result}")
    return result


# 파일 저장 (옵션)
def save_file(rows: List[Dict], keyword: str, fname: str):
    os.makedirs("txt", exist_ok=True)
    path = os.path.join("txt", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"--- {keyword} ---\n")
        for r in rows:
            f.write(f"{r['name']} | {r['addr']} | {r.get('score')} | {r.get('menus')}\n") # 여기 메뉴 못가져오는데 menus 삭제할까?
    logging.info(f"{path} 저장 완료")


# FastAPI 엔드포인트
@app.get("/restaurants")  # 목록만
def list_restaurants(keyword: str = Query(..., description="검색어")):
    try:
        rows = get_restaurants(keyword)
        save_file(rows, keyword, "restaurants.txt")
        return rows
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/restaurants-with-menus")  # 목록 + 메뉴
def list_restaurants_with_menus(keyword: str = Query(...)):
    try:
        rows = get_restaurants(keyword) 

        fail_count = 0               # ← 실패 횟수 카운터
        MAX_FAIL  = 5                # ← 연속 실패 허용 한도

        for r in rows:
            try:
                logging.info(f"{r['name']} 메뉴 크롤링 시작")
                r["menus"] = get_menu_items_by_dom(r["v_rid"])
            except Exception as e:
                logging.warning(f"메뉴 크롤링 실패(rid={r['v_rid']}): {e}")
                r["menus"] = []
                fail_count += 1

                if fail_count >= MAX_FAIL:
                    logging.warning("실패가 많아 전체 크롤링 중단")
                    break            # → 더 이상 크롤링 진행하지 않고 루프 탈출
            else:
                fail_count = 0       # 성공하면 실패 카운터 리셋

        save_file(rows, keyword, "restaurants_with_menu.txt")
        return rows

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})