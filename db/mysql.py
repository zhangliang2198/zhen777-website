from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

database_config = {
    "host": "8.219.53.116",
    "user": "root",
    "password": "Meili163!!",
    "database": "openai",
}

database_config_shop = {
    "host": "8.219.53.116",
    "user": "root",
    "password": "Meili163!!",
    "database": "openai",
}

# 创建一个连接池
db_pool = MySQLConnectionPool(pool_name="openai", pool_size=5, **database_config)
db_pool_shop = MySQLConnectionPool(pool_name="yph", pool_size=5, **database_config)

DATABASE_URL = "mysql+mysqlconnector://root:Meili163!!@8.219.53.116/openai"
DATABASE_URL_YPH = "mysql+mysqlconnector://root:Meili163!!@8.219.53.116/openai"

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# # 创建一个连接池
# db_pool = MySQLConnectionPool(pool_name="openai", pool_size=5, **database_config)
# db_pool_shop = MySQLConnectionPool(pool_name="yph", pool_size=5, **database_config)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
