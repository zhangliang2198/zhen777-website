from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

Base = declarative_base()


# SQLAlchemy Task Model
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    func = Column(String(100))
    cron = Column(String(50))
    is_active = Column(Boolean, default=True)


# Pydantic TaskCreate Model
class TaskCreate(BaseModel):
    name: str
    func: str
    cron: str
    is_active: Optional[bool] = True


# Pydantic TaskOut Model
class TaskOut(BaseModel):
    id: int
    name: str
    func: str
    cron: str
    is_active: bool

    class Config:
        orm_mode = True


class TaskUpdate(BaseModel):
    name: str
    func: str
    cron: str

    class Config:
        orm_mode = True


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Task).offset(skip).limit(limit).all()


def create_task(db: Session, task: TaskCreate):
    db_task = Task(name=task.name, func=task.func, cron=task.cron, is_active=task.is_active)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
        return True
    return False
