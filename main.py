from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.users import router as users_router
from ai_modules.apis import router as ai_router
from ai_modules.agents import router as agents_router
from routers.gmail_api import router as gmail_router
from database.db_config import Base, engine
import asyncio
from contextlib import asynccontextmanager
import redis.asyncio as redis
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor



resource = Resource(attributes={SERVICE_NAME: "fastapi-service"})

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


resource = Resource(
    attributes={
        SERVICE_NAME: "ticagent-fastapi"
    }
)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",
)

provider = TracerProvider(
    resource=resource
)

processor = BatchSpanProcessor(
    otlp_exporter
)

provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
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
FastAPIInstrumentor.instrument_app(app)


# Register your router globally
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_router)
app.include_router(agents_router)
app.include_router(gmail_router)

@app.get("/")
def root():
    return {"message": "API is running"}





if __name__ == "__main__":
    asyncio.run(init_db())