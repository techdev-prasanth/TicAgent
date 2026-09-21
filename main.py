from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.users import router as users_router
from ai_modules.apis import router as ai_router
from ai_modules.agents import router as agents_router
from db_config import Base, engine
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis


redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


    global redis_client
    redis_client = redis.Redis(host="localhost",decode_responses=True,port=6379,db=2)
    
    try:
        await redis_client.ping()
        app.state.redis = redis_client
    except redis.ConnectionError():
        app.state.redis = None
        await redis_client.aclose()


    yield

    if app.state.redis:
        await app.state.redis.aclose()
        



app = FastAPI(lifespan=lifespan)

# Register your router globally
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_router)
app.include_router(agents_router)

@app.get("/")
def root():
    return {"message": "API is running"}





if __name__ == "__main__":
    asyncio.run(init_db())