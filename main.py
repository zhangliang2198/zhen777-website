import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db.mysql import get_db
from modules.sys_task import get_tasks
from router.scheduler import router_task, scheduler
from router.user_router import router
from router.yph_shop_router import router_yph
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
    db = next(get_db())
    tasks = get_tasks(db, 0, 1000)

    # 先清理掉所有的
    scheduler.remove_all_jobs()
    for task in tasks:
        if task.is_active:
            scheduler.add_job(
                func=get_function_from_string(task.func),
                trigger=IntervalTrigger(seconds=int(task.cron)),
                id=str(task.id),
                replace_existing=True
            )

    scheduler.start()


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000)
