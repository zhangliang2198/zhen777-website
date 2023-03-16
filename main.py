import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from router.user_router import router

# 应用
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000)
