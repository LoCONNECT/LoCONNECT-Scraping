from fastapi import FastAPI
from app.api.main_controllers import router as restaurant_router

app = FastAPI()
app.include_router(restaurant_router, prefix="/restaurants")
    
    # pthon 3.13버전 설치
    # 초기 클론 pip install poetry
    # (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python - 터미널에 입력
    # poetry install  === npm i (팀원 각자 가상환경 만들어야 함)
    # 서버 키는 명령어 poetry run uvicorn app.main:app --reload (= FastAPI 실행)
    # ㅇㅇ 안쓰는 것들 다 삭제하자



