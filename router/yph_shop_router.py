from fastapi import Depends, Request, status, Response, APIRouter
from sqlalchemy import text
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from db.mysql import get_db_yph

router_yph = APIRouter()

templates = Jinja2Templates(directory="templates")


@router_yph.get("/users", response_class=HTMLResponse)
async def get_user(request: Request, response: Response, db: Session = Depends(get_db_yph)):
    query = text(f"select * from system_users limit :start,:size")
    datas = db.execute(query, {"start": 0, "size": 15}).all()
    return templates.TemplateResponse("yph_user.html", {"request": request, "error": "", "data": datas})
