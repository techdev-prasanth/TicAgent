from sqlalchemy import Column , Integer, String , DateTime  , Text  , ForeignKey
from sqlalchemy.orm import relationship
from db_config import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column ,relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID

class TicketCategory(Base):
    __tablename__ = "ticketcategories"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,index=True,unique=True,
                                               nullable=False,default=uuid.uuid4)
    
    name : Mapped[str] = mapped_column(String(100))
    code : Mapped[str] = mapped_column(String(100))
    description : Mapped[str] = mapped_column(Text)
    created_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)
    updated_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now,onupdate=datetime.now)


    def __str__(self):
        return str(self.id)
    


class Ticket(Base):
    __tablename__ = "ticket"
    
    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,
                                               default=uuid.uuid4)

    
    customer_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                    ForeignKey("users.id"), nullable=False)

    customer_message : Mapped[str] = mapped_column(Text)
    category_code : Mapped[str | None] = mapped_column(String(100))
    consent_given : Mapped[str | None] = mapped_column(String(100))
    priority : Mapped[str | None] = mapped_column(String(100))

    description : Mapped[str | None] = mapped_column(Text)

    created_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)
    updated_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now,onupdate=datetime.now)



    customer : Mapped["User"] = relationship("User",back_populates="tickets")

    def __str__(self):
        return str(self.id)
   