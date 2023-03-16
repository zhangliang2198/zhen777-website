import redis

redis_config = {
    "host": "8.219.53.116",
    "port": 6379,  # 通常是 6379
    "db": 5,  # 选择一个数据库（0 到 15）
    "password": "Meili163!!"
}

redis_client = redis.StrictRedis(**redis_config)
