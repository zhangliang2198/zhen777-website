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
