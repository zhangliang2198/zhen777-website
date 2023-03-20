import redis

redis_config = {
    "host": "127.0.0.1",
    "port": 6379,  # 通常是 6379
    "db": 5,  # 选择一个数据库（0 到 15）
    "password": "diwkdfoqwiefoqwinfo1f9qw898qw1f98qwf9qwef19"
}

redis_client = redis.StrictRedis(**redis_config)
