from fastapi import Depends, Request, status, Response, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from fastapi import Form
from starlette.responses import HTMLResponse
from db.mysql import db_pool
from logger import logger
from modules.user_module import authenticate_user, create_access_token, get_current_user, User, save_token

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("首页面访问")
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if user:
        access_token = create_access_token(data={"sub": username})
        save_token(user['id'], access_token)  # 保存 JWT 到数据库
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
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists."})

    hashed_password = pwd_context.hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    connection.commit()
    cursor.close()
    connection.close()

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "current_user": current_user})
