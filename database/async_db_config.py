from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv(override=True)

import os

ASYNC_DB_URL = os.getenv("ASYNC_DB_URL")

async_engine = create_async_engine(ASYNC_DB_URL,poolclass=NullPool)

async_session = async_sessionmaker(bind=async_engine,class_=AsyncSession,expire_on_commit=False) 


async def get_async_session():
    async with async_session() as db:
        yield db
