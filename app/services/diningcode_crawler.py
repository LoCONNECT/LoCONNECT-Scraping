import os
import logging, requests
from typing import List, Dict

BASE_URL = "https://www.diningcode.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 다이닝코드 -> 가게 리스트들에는 관대함, 상세 가게 정보는 봇이 차단

def get_restaurants(keyword: str) -> List[Dict]:
    logging.info("DiningCode 식당 목록 수집 시작")
    page, size = 1, 20
    seen_rids, result = set(), []
    MAX_REPEAT, repeated = 3, 0

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
            logging.error(f"API 오류: {r.status_code}")
            break

        items = (
            r.json()
            .get("result_data", {})
            .get("poi_section", {})
            .get("list", [])
        )
        if not items:
            break

        page_rids = [it["v_rid"] for it in items]
        if all(rid in seen_rids for rid in page_rids):
            repeated += 1
            if repeated >= MAX_REPEAT:
                break
        else:
            repeated = 0

        for it in items:
            rid = it["v_rid"]
            if rid in seen_rids:
                continue
            seen_rids.add(rid)
            result.append(
                {
                    "name": it.get("nm"),
                    "addr": it.get("addr"),
                    "score": it.get("score"),
                }
            )

        page += 1

    logging.info(f"총 {len(result)}곳 수집 완료")
    return result

def save_file(rows: List[Dict], keyword: str, fname: str):
    os.makedirs("txt", exist_ok=True)
    path = os.path.join("txt", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"--- {keyword} ---\n")
        for r in rows:
            f.write(f"{r['name']} | {r['addr']} | {r.get('score')} \n")
            for m in r.get("menus", []):
                f.write(f"    └ {m['name']} - {m.get('price', '가격 없음')}\n")
    print(f"[INFO] {path} 저장 완료")