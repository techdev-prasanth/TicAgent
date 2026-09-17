from sqlalchemy import Column , String , Integer  , DateTime , func 
from sqlalchemy.orm import relationship
from db_config import engine,local_session,Base
import uuid
from sqlalchemy.orm import Mapped , mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ai_modules.models import Ticket
class User(Base):
    __tablename__ = "users"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    fullname : Mapped[str] = mapped_column(String(255),nullable=False)
    username : Mapped[str] = mapped_column(String(255))
    email : Mapped[str] = mapped_column(String(255))
    password : Mapped[str] = mapped_column(String(255),nullable=False)



    tickets : Mapped["Ticket"] = relationship("Ticket",back_populates="customer",cascade="all , delete-orphan")
    
    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        server_onupdate=func.now()
        )


    

    def __str__(self):
        return str(self.id)