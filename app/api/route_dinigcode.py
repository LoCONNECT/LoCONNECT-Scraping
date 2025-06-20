from fastapi import APIRouter, Query
from app.services.diningcode_crawler import crawl_menu

router = APIRouter()

@router.get("/diningcode")
def get_diningcode_menu(url: str = Query(..., description="다이닝코드 식당 상세 URL")):
    data = crawl_menu(url)
    return {"menus": data}