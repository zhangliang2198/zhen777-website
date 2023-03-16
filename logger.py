import logging
import mysql.connector
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.mysql import db_pool, get_db


class MySQLHandler(logging.Handler):
    def __init__(self, db: Session):
        logging.Handler.__init__(self)
        self.db = db

    def emit(self, record):
        if not record:
            return
        query = text(f"INSERT INTO log (logger_name, level, message) VALUES (:logger_name, :level, :message)")
        self.db.execute(query, {"logger_name": record.name, "message": record.getMessage(), "level": record.levelname})
        self.db.commit()


logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.DEBUG)
# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 将自定义的 MySQLHandler 添加到日志处理器中
mysql_handler = MySQLHandler(next(get_db()))
mysql_handler.setFormatter(formatter)
logger.addHandler(mysql_handler)

# 如果还需要在控制台输出日志，添加以下代码
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
