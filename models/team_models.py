from sqlalchemy.orm import Mapped , mapped_column 
from database.db_config import get_session ,Base
from sqlalchemy import String , Integer , Text , ForeignKey 
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Teamcategory(Base):
    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),nullable=False,primary_key=True,index=True,unique=True)
    name : Mapped[str] = mapped_column(String(255),nullable=False,unique=True)
    description : Mapped[str] = mapped_column(Text,nullable=True)


class Team(Base):
    team_category_id : Mapped[Teamcategory] = mapped_column()
