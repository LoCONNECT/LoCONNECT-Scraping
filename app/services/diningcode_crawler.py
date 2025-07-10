import os
import logging
import requests
import json
from typing import List, Dict

BASE_URL = "https://www.diningcode.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_restaurants(keyword: str) -> List[Dict]:
    logging.info(f"[START] '{keyword}' 지역 식당 목록 수집")
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
            logging.error(f"[ERROR] API 오류: {r.status_code}")
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
                    "menus": [],  # 나중에 Kakao/Naver에서 채워줄 수 있게 기본 추가
                }
            )

        page += 1

    logging.info(f"[DONE] {keyword} - 총 {len(result)}곳 수집 완료")
    return result


def save_file(rows: List[Dict], region: str):
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", f"menus-{region}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] {path} 저장 완료")
