import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from router.scheduler import router_task
from router.user_router import router
from router.yph_shop_router import router_yph

# 应用
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.include_router(router_yph)
app.include_router(router_task)
if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000)
