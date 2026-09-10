from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base 


DB_URL = "sqlite:///demo.db"



engine = create_engine(DB_URL)

local_session  = sessionmaker(bind=engine,autoflush=True,autocommit=False)

Base = declarative_base()



def get_session():
    db = local_session()

    try:
        yield db
    finally:
        db.close()
