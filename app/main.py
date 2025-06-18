from fastapi import FastAPI

app = FastAPI()

#Main, Nest.Js에서 Main.ts

#venv가 아닌 poetry를 사용한 이유
#의존성 충돌을 방지하고 협업시 패키지 충돌을 방지하기 위해서 사용

@app.get("/")
def read_root():
    return {"hi"}

# BeautifulSoup 사용 예시 코드
# youtube,naver는 query에 keword를 담아서 검색

# from fastapi import FastAPI
# from bs4 import BeautifulSoup
# import requests

# app = FastAPI()

# @app.get("/naver-news")
# def get_naver_news(query: str = "우주"):
#     url = f"https://search.naver.com/search.naver?where=news&query={query}"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#         "Referer": "https://www.naver.com",
#         "Accept-Language": "ko-KR,ko;q=0.9"
#     }
#     res = requests.get(url, headers=headers)
#     soup = BeautifulSoup(res.text, "html.parser")

#     titles = []
#     for a in soup.find_all("a"):
#         span = a.find("span")
#         if span and query in span.text:
#             titles.append(span.text.strip())

#     if not titles:
#         return {"message": "뉴스 제목을 찾지 못했습니다.", "results": []}

#     # 파일 저장
#     with open("news_titles.txt", "w", encoding="utf-8") as f:
#         for title in titles:
#             f.write(f"{title}\n")

#     return {"titles": titles, "message": "뉴스 제목 저장 완료"}
