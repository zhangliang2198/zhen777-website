from fastapi import Depends, Request, status, Response, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from fastapi import Form
from sqlalchemy import text
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session
from crfsutil import generate_csrf_token, validate_csrf_token
from db.mysql import db_pool, get_db
from logger import logger
from modules.user_module import authenticate_user, create_access_token, get_current_user, User, save_token, \
    save_token_to_redis, is_authenticated, delete_token_from_redis

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, response: Response):
    authenticated, decoded_token = is_authenticated(request)
    if authenticated:
        return RedirectResponse(url=f"/dashboard?username={decoded_token}", status_code=303)
    else:
        return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    authenticated, decoded_token = is_authenticated(request)
    if authenticated:
        return RedirectResponse(url=f"/dashboard?username={decoded_token}", status_code=303)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("login.html", {"request": request, "csrf_token": csrf_token, "error": None})
    response.set_cookie("csrf_token", csrf_token, httponly=True)
    logger.info("登录页面访问")
    return response


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...),
                db: Session = Depends(get_db)):
    client_csrf_token = request.cookies.get("csrf_token")
    if not client_csrf_token or not validate_csrf_token(csrf_token, client_csrf_token):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid CSRF token."})
    user = authenticate_user(username, password, db)
    if user:
        access_token = create_access_token(data={"sub": username})
        save_token(user.id, access_token,db)  # 保存 JWT 到数据库
        save_token_to_redis(user.username, access_token)  # 保存 JWT 到 Redis
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
            path="/",
        )
        logger.info(f"用户登录成功:%s", username)
        return response
    else:
        logger.warn(f"用户登录失败:%s", username)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password."})


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...),
                   db: Session = Depends(get_db)):
    query = text(f"SELECT * FROM users WHERE username=:username")
    existing_user = db.execute(query, {"username": username}).fetchone()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists."})
    hashed_password = pwd_context.hash(password)

    db_user = User(username=username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.get("/logout")
async def logout(response: Response, request: Request):
    authenticated, decoded_token = is_authenticated(request)
    response.delete_cookie("access_token")
    delete_token_from_redis(decoded_token)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "current_user": current_user})
