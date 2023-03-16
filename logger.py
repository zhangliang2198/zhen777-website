import logging
import mysql.connector
from db.mysql import db_pool

class MySQLHandler(logging.Handler):
    def __init__(self, db_pool):
        logging.Handler.__init__(self)
        self.db_pool = db_pool

    def emit(self, record):
        if not record:
            return

        connection = self.db_pool.get_connection()
        cursor = connection.cursor()
        query = "INSERT INTO log (logger_name, level, message) VALUES (%s, %s, %s)"
        cursor.execute(query, (record.name, record.levelname, record.getMessage()))
        connection.commit()
        cursor.close()
        connection.close()


logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.DEBUG)
# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 将自定义的 MySQLHandler 添加到日志处理器中
mysql_handler = MySQLHandler(db_pool)
mysql_handler.setFormatter(formatter)
logger.addHandler(mysql_handler)

# 如果还需要在控制台输出日志，添加以下代码
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
