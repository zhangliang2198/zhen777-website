from fastapi import Request, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, Dict
import os
import datetime

from db.mysql import db_pool
from db.redis import redis_client

# 配置
SECRET_KEY = os.environ.get("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 数据库连接

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    id: Optional[int]
    username: str
    cellphone: Optional[str]
    email: Optional[str]
    email_verified_at: Optional[str]
    state: Optional[str]
    nickname: Optional[str]
    description: Optional[str]
    gender: Optional[str]
    avatar: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    password: Optional[str]


def get_user(username: str):
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM users WHERE username=%s", (username,))
    user_record = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_record


# 验证用户
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user["password"]):
        return False
    return user


# 创建访问令牌
def create_access_token(data: Dict[str, str], expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def save_token(user_id: int, token: str):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO tokens (user_id, token) VALUES (%s, %s)"
    cursor.execute(query, (user_id, token))
    connection.commit()
    cursor.close()
    connection.close()


# 获取当前用户
async def get_current_user(request: Request, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(access_token.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


def save_token_to_redis(username: str, token: str, expire: int = 1800):
    redis_client.set(f"user_token:{username}:jwt", token, ex=expire)


def delete_token_from_redis(username: str):
    redis_client.delete(f"user_token:{username}:jwt")


def is_authenticated(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return False, None
    try:
        payload = jwt.decode(access_token.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        username = payload["sub"]
    except:
        return False, None

    # 从 Redis 中获取存储的 JWT
    stored_jwt = redis_client.get(f"user_token:{username}:jwt")
    if not stored_jwt or stored_jwt.decode() != access_token.split(" ")[1]:
        return False, None

    return True, username
