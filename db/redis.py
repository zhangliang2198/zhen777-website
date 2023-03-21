import redis

redis_config = {
    "host": "172.26.164.93",
    "port": 6379,  # 通常是 6379
    "db": 5,  # 选择一个数据库（0 到 15）
    "password": "SZlanyou@2022"
}

redis_client = redis.StrictRedis(**redis_config)
