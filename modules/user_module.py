from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from db.mysql import get_db_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    # id: int
    username: str
    password: str
    # cellphone: str
    # email: str
    # email_verified_at: str
    # state: str
    # nickname: str
    # description: str
    # gender: str
    # avatar: str
    # created_at: int
    # updated_at: int
    # password: Optional[str]


def get_user(username: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    connection.close()
    return user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if verify_password(password, user["password"]):
        return user


def create_user(username: str, password: str):
    hashed_password = pwd_context.hash(password)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed_password),
    )
    connection.commit()
    connection.close()
