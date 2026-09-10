from sqlalchemy import Column , String , Integer
from db_config import engine,local_session,Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,unique=True,index=True,nullable=False)
    full_name = Column(String(255),nullable=False)
    username = Column(String(255),nullable=False)
    email= Column(String(255),nullable=False,unique=True)
    password = Column(String(255),nullable=False)


    