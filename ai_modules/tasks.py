from worker import celery_app
from ai_modules.agents import workflow
from ai_modules.schema import CustomerMessage
from database.async_db_config import AsyncSession , async_engine , async_session , get_async_session
from models.auth_models import User
from utils.security import get_current_user
import asyncio
import uuid
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from utils.dependencies import get_redis , get_redis_client
from fastapi import Depends

async def run_workflow(message : str , user_id : uuid.UUID):

    client = get_redis_client()
    try:
        async with async_session() as session:


            config = {
                    "configurable": {
                        "db":session,
                        "cache":client
                    }
                }

            result = await workflow.ainvoke({
                    "customer_message":message,
                        "customer_id":user_id
                        
                },
                config=config)


            return jsonable_encoder(result)

    finally:
        if client is None and hasattr(client,'aclose'):
            await client.aclose()

        await async_engine.dispose()

@celery_app.task
def proccess_message(message,user_id,session=None):

    result = asyncio.run(run_workflow(message,user_id))

    print("\nHi this demo() from celery .......", result, "\n")

    return result