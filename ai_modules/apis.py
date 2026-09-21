from fastapi import APIRouter , Depends
from .schema import TicketCategorySchema , TicketCategoryResponse , CustomerMessage , TicketCreate
from db_config import get_session
from ai_modules.models import TicketCategory , Ticket 
from models.auth_models import User
from fastapi.responses import JSONResponse
from fastapi import status
import uuid
from sqlalchemy.orm import Session 
from sqlalchemy import select
from ai_modules.agents import workflow
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from utils.security import get_current_user
from ai_modules.tasks import proccess_message
from utils.dependencies import get_redis , get_redis_client
import redis.asyncio as redis
import json
from async_db_config import get_async_session



router  =APIRouter(prefix="/api/v1/tickets")


redis_client = None

@router.get("/categories/")
async def get_category(session : Session = Depends(get_session),
                cache = Depends(get_redis)):

    KEY , TTL = "categories:all" , 300


    if cache:
        try:
            cached = await cache.get(KEY)
            if cached:
                print("comes from cahce")
                return json.loads(cached)

        except redis.RedisError as e:
            return {
                "message":f"cache is error {e}"
            }

    result = session.execute(select(TicketCategory))
    payload = [TicketCategoryResponse.model_validate(c).model_dump(mode="json") for c in result.scalars().all() ]

    await cache.set(KEY,json.dumps(payload), ex=TTL)

    return payload

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


@router.get("/users-tickets/")
def fetch_users_tickets(session : Session = Depends(get_session),user : User = Depends(get_current_user)):
     
    tickets = (
        session.query(Ticket)
        .filter(Ticket.customer_id == user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return {
        "message":"fetched",
        "data":tickets
    }
    

@router.post("/messages")
async def customer_email(request: CustomerMessage, session: AsyncSession = Depends(get_async_session),
                         user : User =  Depends(get_current_user),
                         cache = Depends(get_redis)):


    # state = {"customer_message":request.message}

    # db_gen = session
    # db = next(db_gen)

  
    print("User",user)
    task = proccess_message.delay(message=request.message,user_id=user.id)

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Message sent to background queue successfully."
    }

