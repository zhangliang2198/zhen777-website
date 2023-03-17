from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from modules.sys_task import Task, get_tasks, TaskCreate, TaskOut, TaskUpdate
from db.mysql import get_db
from utils import get_function_from_string

router_task = APIRouter()
jobstores = {
    'default': SQLAlchemyJobStore(url='mysql+mysqlconnector://root:Meili163!!@8.219.53.116/openai')
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
templates = Jinja2Templates(directory="templates")


@router_task.get("/tasks", response_class=HTMLResponse)
async def display_tasks(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = get_tasks(db, skip=skip, limit=limit)
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks})


@router_task.post("/tasks/create", response_model=TaskOut)
async def create_task(task_name: str = Form(...),
                      task_func: str = Form(...),
                      task_cron: str = Form(...),
                      db: Session = Depends(get_db)
                      ):
    db_task = Task(name=task_name, func=task_func, cron=task_cron, is_active=0)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    task_out = TaskOut.from_orm(db_task)  # 将 SQLAlchemy 模型转换为 Pydantic 模型
    return task_out


@router_task.post("/tasks/{task_id}/start")
async def start_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler.add_job(
        get_function_from_string(task.func),
        CronTrigger.from_crontab(task.cron),
        id=str(task.id),
        replace_existing=True
    )

    return {"detail": f"Task {task.id} started"}


@router_task.post("/tasks/{task_id}/stop")
async def stop_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler.remove_job(str(task.id))

    return {"detail": f"Task {task.id} stopped"}


@router_task.post("/tasks/{task_id}/pause")
async def pause_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler.pause_job(str(task.id))

    return {"detail": f"Task {task.id} paused"}


@router_task.post("/tasks/{task_id}/resume")
async def resume_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler.resume_job(str(task.id))

    return {"detail": f"Task {task.id} resumed"}


@router_task.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler.remove_job(str(task.id))
    db.delete(task)
    db.commit()

    return {"detail": f"Task {task.id} deleted"}


@router_task.get("/tasks/{task_id}/edit", tags=["tasks"])
async def edit_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router_task.post("/tasks/{task_id}/update", tags=["tasks"])
async def update_task(task_id: int,
                      task_name: str = Form(...),
                      task_func: str = Form(...),
                      task_cron: str = Form(...),
                      db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.name = task_name
    task.func = task_func
    task.cron = task_cron

    db.add(task)
    db.commit()
    db.refresh(task)

    return {"message": "Task updated successfully", "task": task}
