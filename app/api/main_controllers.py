from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.diningcode_crawler import get_restaurants, save_file
from app.services.kakao_crawler import (
    get_kakao_place_id,
    get_menu_from_kakao,
)
from app.services.naver_crawler import ( 
    search_naver_place_id, 
    get_menu_from_naver
    )
router = APIRouter()


@router.get("")
async def list_restaurants(keyword: str = Query(..., description="검색어")):
    try:
        rows = get_restaurants(keyword)

        for row in rows:
            try:
                place_id = get_kakao_place_id(row["name"], row["addr"])
                row["menus"] = []

                if place_id:
                    try:
                        row["menus"] = get_menu_from_kakao(place_id)
                        print(f"[DEBUG] {row['name']} ✚ 메뉴 {len(row['menus'])}개 (Kakao)")
                    except Exception as e:
                        print(f"[WARN] {row['name']} Kakao 메뉴 실패 → {e}")
                else:
                    print(f"[MISS] {row['name']} place_id 못 찾음 (Kakao)")

                # Kakao 실패 or 결과 없음 → Naver fallback
                if not row["menus"]:
                    try:
                        place_link = search_naver_place_id(f"{row['name']} {row['addr']}")
                        if place_link:
                            row["menus"] = get_menu_from_naver(place_link)
                            print(f"[DEBUG] {row['name']} ✚ 메뉴 {len(row['menus'])}개 (Naver)")
                        else:
                            print(f"[MISS] {row['name']} Naver 검색 실패")
                    except Exception as e:
                        print(f"[WARN] {row['name']} Naver 메뉴 실패 → {e}")

            except Exception as e:
                row["menus"] = []
                print(f"[FATAL] {row['name']} 전체 실패 → {e}")

        save_file(rows, keyword, "restaurants_with_menus.txt")
        return rows

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})