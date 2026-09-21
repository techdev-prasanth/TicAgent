from fastapi import Request
import redis.asyncio as redis

def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host="localhost",
        port=6379,
        db=2,
        decode_responses=True
    )

def get_redis(request: Request):
    return request.app.state.redis

