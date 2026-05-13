# db\Redis.py
import redis
import os

r = redis.Redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)


r.set("Base REDIS", "Conectada")
print(r.get("Base REDIS"))