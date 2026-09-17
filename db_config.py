from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base 
from dotenv import load_dotenv
import os
load_dotenv(override=True)



DB_URL = os.getenv("DB_URL")
print("DB",DB_URL)
engine = create_engine(DB_URL)

local_session  = sessionmaker(bind=engine,autoflush=True,autocommit=False)

Base = declarative_base()



def get_session():
    db = local_session()

    try:
        yield db
    finally:
        db.close()
