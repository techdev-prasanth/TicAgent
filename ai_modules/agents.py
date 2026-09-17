import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langgraph.graph import StateGraph , START , END
from langgraph.prebuilt import create_react_agent
from groq import Groq
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict
from sqlalchemy import text , select
from db_config import  get_session
from sqlalchemy.orm import Session 
from fastapi import Depends , APIRouter
from ai_modules.models import TicketCategory , Ticket
from ai_modules.schema import TicketCategoryResponse , TicketClassfication
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.runnables import RunnableConfig
load_dotenv()


router = APIRouter(prefix="/agents")

model = ChatGroq(model="openai/gpt-oss-120b",temperature=0.2)




class State(TypedDict):
    customer_id : uuid
    customer_message : str
    flag : bool
    classification : TicketClassfication | None
    message : str

def santize_content(state: State):
    print("")
    print("santize_content starts 1")
    print("")
    customer_message = state["customer_message"].lower()
    BLACKLISTED_WORDS = [
        "Hack",
        "Delete the account",
        "forget the previous chat",
        "forget the prompt",
        "ACT as",
        "employee details"
    ]

    flag = any(i.lower() in customer_message for i in BLACKLISTED_WORDS) 
    return {"flag":flag}


# async def fetch_user(user_id: int,)

def sanitize_router(state: State):
    print("")
    print("sanitize_router starts 2")
    print("")
    print()
    print("state of santize ",state["flag"])
    print() 
    return "reject" if state["flag"] == True else "classify"

def reject_message(state : State):
    print("")
    print("reject_message starts 3")
    print("")
    print("Not Allowed")
    print("classification",state["classification"])
    return {"classfication":None}

async def classify_customer_mail(state: State, config : RunnableConfig):
    print("")
    print("classify_customer_mail starts 4")
    print("")
    db : AsyncSession = config["configurable"]["db"]    
    customer_message = state["customer_message"]

    stmt = select(TicketCategory)
    result = db.execute(stmt)

    values = result.scalars().all()

    validate_values = [TicketCategoryResponse.model_validate(i) for i in values]
    categories_prompt = "".join(
        f"- Code : {i.code} | Name : {i.name} | category : {i.description}"
        for i in validate_values
    )

    system_prompt = f"""
    You are an AI support ticket routing assistant.
    Analyze the incoming customer message and perform classification.

    ALLOWED CATEGORIES:
    {categories_prompt}

    RULES:
    1. Select EXACTLY ONE category_code from the allowed list above.
    2. Assess urgency and assign priority (Low, Medium, High, Critical).
    3. Detect customer sentiment (Positive, Neutral, Frustrated, Angry).
    4. If the message does not clearly match any specific category code, select "GENERAL_INQUIRY".
    """

    messages = [

        ("system",system_prompt),
        ("human",customer_message)
    ]
    structed_responee = model.with_structured_output(TicketClassfication)
    classification_response = await structed_responee.ainvoke(messages)
    print("Response : ",classification_response)
    return {"classification":classification_response}


def create_ticket(state : State, config: RunnableConfig):

    print("")
    print("create ticke has been created from agents 5")
    print("")
     
    db = config["configurable"]["db"]


   
    response = state["classification"]

    print("response",response)

    ticket = Ticket(
        customer_id = state["customer_id"],
        customer_message = state["customer_message"],
        priority = response.priority,
        consent_given = response.sentiment,
        category_code= response.category_code,
        description = response.description

    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    print("Ticket has been created")
    return {"message":response}

builder = StateGraph(State)

builder.add_node("santize_content",santize_content)
builder.add_node("reject_message",reject_message)
builder.add_node("classify_customer_mail",classify_customer_mail)
builder.add_node("create_ticket",create_ticket)



builder.add_edge(START,"santize_content")

builder.add_conditional_edges("santize_content",
                    sanitize_router,
                    {"classify":"classify_customer_mail",
                    "reject": "reject_message"})

builder.add_edge("reject_message",END)
builder.add_edge("classify_customer_mail","create_ticket")
builder.add_edge("create_ticket",END)


workflow = builder.compile()






# if __name__ == "__main__":
#     try:
#         app.invoke({"customer_message":email},config={"configurable":{"db":db}})
#     finally:
#         db_gen.close()