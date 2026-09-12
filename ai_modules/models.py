from sqlalchemy import Column , Integer, String , DateTime
from db_config import Base
from datetime import datetime

class TicketCategory(Base):
    __tablename__ = "ticketcategories"

    id = Column(Integer,primary_key=True,index=True,nullable=False,unique=True)
    name = Column(String(100),nullable=False)
    code = Column(String(100))
    description = Column(String(255))
    created_at = Column(DateTime,default=datetime.now)
    updated_at = Column(DateTime,default=datetime.now,onupdate=datetime.now)



class Ticket(Base):
    __tablename__ = "ticket"
    
    id = Column(Integer,primary_key=True,index=True,nullable=False,unique=True)
    customer_id = Column(String(100),nullable=False)
    customer_message = Column(String(100))
    category_code = Column(String(255))
    consent_given = Column(DateTime)

    
    created_at = Column(DateTime,default=datetime.now)
    updated_at = Column(DateTime,default=datetime.now,onupdate=datetime.now)
