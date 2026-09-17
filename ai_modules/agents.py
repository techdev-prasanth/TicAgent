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
from langchain_core.runnables import RunnableConfig
load_dotenv()


router = APIRouter(prefix="/agents")

model = ChatGroq(model="openai/gpt-oss-120b",temperature=0.2)




class State(TypedDict):
    customer_message : str
    flag : bool
    classification : TicketClassfication | None

def santize_content(state: State):
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
    print()
    print("state of santize ",state["flag"])
    print() 
    return "reject" if state["flag"] else "classify"

def reject_message(state : State):
    print("Not Allowed")
    print("classification",state["classification"])
    return {"classfication":None}

def classify_customer_mail(state: State, config : RunnableConfig):
    db : Session = config["configurable"]["db"]    
    customer_message = state["customer_message"]
    values = db.query(TicketCategory).all()

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
    classification_response =  structed_responee.invoke(messages)
    print("Response : ",classification_response)
    return {"classification":classification_response}


def create_ticket(state : State, config: RunnableConfig):

    response = state["classification"]

    ticket = Ticket(
        customer_id = str(uuid.uuid4),
        customer_message = state["customer_message"],
        consent_given = response
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    print("Ticket has been created")
    return "Added"


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

builder.add_edge("classify_customer_mail",END)
builder.add_edge("create_ticket",END)
builder.add_edge("reject_message",END)


email = """
        Dear Sir/Madam,

        i tried to login 3 time in a row , but still it shows enter valid email , even though my mail id is correct.
        help me to fix it , i'm really fed up , asap fix the issue or give me solution , or else i will file a law suite against your company
        Thank you.

        Best regards,
        Prasanth
        """


app = builder.compile()


db_gen = get_session()
db = next(db_gen)





if __name__ == "__main__":
    try:
        app.invoke({"customer_message":email},config={"configurable":{"db":db}})
    finally:
        db_gen.close()