from fastapi import APIRouter , Depends
from .schema import TicketCategorySchema , TicketCategoryResponse
from db_config import get_session
from .models import TicketCategory
from fastapi.responses import JSONResponse
from fastapi import status


from sqlalchemy.orm import Session
router  =APIRouter(prefix="/tickets")



@router.get("/category")
def get_category(session : Session = Depends(get_session)):
    data = session.query(TicketCategory).all()

    return data


@router.post("/category")
def create_category(request:TicketCategorySchema, 
                    session : Session= Depends(get_session)):

    ticket_category = TicketCategory(name=request.name,
                   code=request.code,
                    description=request.description
                   )

    session.add(ticket_category)
    session.commit()
    session.refresh(ticket_category)

    return JSONResponse(content="Ticket category created",status_code=status.HTTP_201_CREATED)


