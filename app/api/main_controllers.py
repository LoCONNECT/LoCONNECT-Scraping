from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.diningcode_crawler import get_restaurants, save_file
from app.services.naver_crawler import get_menu_from_naver

router = APIRouter()

@router.get("")
def list_restaurants(keyword: str = Query(..., description="검색어")):
    try:
        rows = get_restaurants(keyword)

        for row in rows:
            try:
                row["menus"] = get_menu_from_naver(row["name"])
                print(f"[DEBUG] {row['name']} → 메뉴 수: {len(row['menus'])}")
            except Exception as e:
                row["menus"] = []
                print(f"[WARN] {row['name']} 메뉴 실패 → {e}") 

        save_file(rows, keyword, "restaurants_with_menus.txt")
        return rows
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})