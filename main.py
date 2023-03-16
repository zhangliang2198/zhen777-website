from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import jwt
import time
from modules.user_module import authenticate_user, get_user, create_user, User
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
SECRET_KEY = "your_secret_key"


@app.get("/")
async def root():
    return "welcome to fastapi skeleton"


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect username or password"},
        )
    access_token = jwt.encode(
        {"sub": user["username"], "exp": int(time.time()) + 3600},
        SECRET_KEY,
        algorithm="HS256",
    )
    response = templates.TemplateResponse("success.html", {"request": request})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    existing_user = get_user(username)
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "用户已经存在"},
        )
    create_user(username, password)
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "success": "用户注册成功"},
    )


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000)
