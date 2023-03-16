import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

database_config = {
    "host": "8.219.53.116",
    "user": "root",
    "password": "Meili163!!",
    "database": "openai",
}

# 创建一个连接池
db_pool = MySQLConnectionPool(pool_name="mypool", pool_size=10, **database_config)
