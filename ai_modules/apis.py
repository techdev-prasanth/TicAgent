from fastapi import APIRouter , Depends
from .schema import TicketCategorySchema , TicketCategoryResponse , CustomerMessage , TicketCreate
from db_config import get_session
from ai_modules.models import TicketCategory , Ticket 
from models.auth_models import User
from fastapi.responses import JSONResponse
from fastapi import status
import uuid
from sqlalchemy.orm import Session
router  =APIRouter(prefix="/api/v1/tickets")



@router.get("/categories/")
def get_category(session : Session = Depends(get_session)):
    data = session.query(TicketCategory).all()
    return data

@router.post("/categories/")
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


@router.delete("/")
def delete_ticket(session : Session = Depends(get_session)):
    tickets = session.query(Ticket).all()

    for i in tickets:

        session.delete(i)
        session.commit()

    return {
        "message":"data fetched",
        "data":tickets
    }

@router.get("/")
def fetch_ticket(session : Session = Depends(get_session)):
    tickets = session.query(Ticket).all()

    return {
        "message":"data fetched",
        "data":tickets
    }



@router.post("/")
def create_ticket(request: TicketCreate,session : Session = Depends(get_session)):

    try:
        ticket = Ticket(customer_id=request.customer_id,
                        customer_message=request.customer_message,
                        category_code=request.category_code,
                        consent_given=request.consent_given)
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return JSONResponse(content="Ticket has been created",status_code=status.HTTP_201_CREATED)  
    except Exception as e:

        return JSONResponse(content=f"There is a problem with creation {e}",status_code=status.HTTP_400_BAD_REQUEST)  


@router.get("/users-tickets/{user_uuid}")
def fetch_users_tickets(user_uuid: uuid.UUID,session : Session = Depends(get_session)):
    print()
    print("UUID",user_uuid)
    tickets = (
        session.query(Ticket)
        .filter(User.id==user_uuid)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets
    