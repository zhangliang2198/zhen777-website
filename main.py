import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db.mysql import get_db
from modules.sys_task import get_tasks
from router.scheduler import router_task, scheduler, init_job
from router.user_router import router
from router.yph_shop_router import router_yph
from similar_product.product_proc import process_product
from utils import get_function_from_string
from apscheduler.triggers.interval import IntervalTrigger

# 应用
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.include_router(router_yph)
app.include_router(router_task)


@app.on_event("startup")
async def on_startup():
    await init_job()
    process_product()


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000)
