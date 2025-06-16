from fastapi import FastAPI

app = FastAPI()

#Main, Nest.Js에서 Main.ts

#venv가 아닌 poetry를 사용한 이유
#의존성 충돌을 방지하고 협업시 패키지 충돌을 방지하기 위해서 사용

@app.get("/")
def read_root():
    return {"hi"}