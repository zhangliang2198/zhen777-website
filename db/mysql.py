from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+mysqlconnector://root:Meili163!!@8.219.53.116/openai"
DATABASE_URL_YPH = "mysql+mysqlconnector://mysqladmin:Mysql6Tvy%402021@172.26.164.94:3306/yph2.0"

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
engine_yph = create_engine(DATABASE_URL_YPH, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal_yph = sessionmaker(autocommit=False, autoflush=False, bind=engine_yph)
Base = declarative_base()


def get_db_yph():
    db = SessionLocal_yph()
    try:
        yield db
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
