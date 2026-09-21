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
from langgraph.prebuilt import ToolNode , tools_condition
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from async_db_config import async_session

import redis.asyncio as redis

from utils.dependencies import get_redis

from langchain_core.runnables import RunnableConfig
load_dotenv()

import json


router = APIRouter(prefix="/agents")

model = ChatGroq(model="openai/gpt-oss-20b",temperature=0.2)


class State(TypedDict):
    customer_id : uuid
    customer_message : str
    flag : bool
    classification : TicketClassfication | None
    message : str
    human_escalation : bool
    consent_given : str


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



def sanitize_router(state: State):

    return "reject" if state["flag"] == True else "classify"





def reject_message(state : State):
    return {"classfication":None}


def set_human_escaltion(state : State):

    result = state["classification"]

    priorty_level = ["High","Critical"]

    sentiment = ["Frustrated","Angry"]

    need_escalation = (result.priority in priorty_level or result.sentiment in sentiment)

    print("need esca",need_escalation)

    return {"human_escalation":need_escalation}


def human_escalation_need(state : State):
    """ based on the sentiment and priority level , set the human_escalation True """
    print("from escaletion need",state["human_escalation"])
    if state["human_escalation"] == True:
        print("state human escaltion : ",True , state["human_escalation"])
        return "human_need"

    print("No human ecslation need")
    return "no_human_need"

def call_human(state : State):
    print("Hi Human , please check this ticket ",state["classification"])


async def get_categories(config: RunnableConfig) -> str:
    KEY = "categories:all"

    configurable = config.get("configurable", {})
    cache = configurable.get("cache")
    db: AsyncSession = configurable["db"]

    categories_list = None

    if cache and hasattr(cache, "get") and callable(cache.get):
        try:
            cached_data = await cache.get(KEY)
            if cached_data:
                raw_data = json.loads(cached_data)
                categories_list = [TicketCategoryResponse.model_validate(item) for item in raw_data]
        except Exception as e:
            categories_list = None

    if categories_list is None:
        print("\n[Cache Miss] Fetching categories from Database...\n")
        stmt = select(TicketCategory)
        result = await db.execute(stmt)
        orm_rows = result.scalars().all()

        categories_list = [TicketCategoryResponse.model_validate(row) for row in orm_rows]

        if cache and hasattr(cache, "set") and callable(cache.set):
            try:
                serializable_data = [cat.model_dump() for cat in categories_list]
                await cache.set(KEY, json.dumps(serializable_data), ex=3600)
            except Exception as e:
                pass
    categories_prompt = "\n".join(
        f"- Code : {cat.code} | Name : {cat.name} | Category : {cat.description}"
        for cat in categories_list
    )

    return categories_prompt
async def classify_customer_mail(state: State, config : RunnableConfig):
    customer_message = state["customer_message"]

    categories_prompt = await get_categories(config=config)

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
    return {"classification":classification_response}


async def create_ticket(state : State, config: RunnableConfig):
    db : AsyncSession = config["configurable"]["db"]
    response = state["classification"]

    ticket = Ticket(
        customer_id = state["customer_id"],
        customer_message = state["customer_message"],
        priority = response.priority,
        consent_given = response.consent_given,
        category_code= response.category_code,
        description = response.description,
        sentiment = response.sentiment

    )

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)


    return response


builder = StateGraph(State)

builder.add_node("santize_content",santize_content)
builder.add_node("reject_message",reject_message)
builder.add_node("classify_customer_mail",classify_customer_mail)
builder.add_node("create_ticket",create_ticket)
builder.add_node("set_human_escaltion",set_human_escaltion)
builder.add_node("call_human",call_human)




builder.add_edge(START,"santize_content")

builder.add_conditional_edges("santize_content",
                    sanitize_router,
                    {"classify":"classify_customer_mail",
                    "reject": "reject_message"},)

builder.add_edge("reject_message",END)

builder.add_edge("classify_customer_mail","create_ticket")
builder.add_edge("create_ticket","set_human_escaltion")

builder.add_conditional_edges("set_human_escaltion",
                              human_escalation_need,
                              {"human_need":"call_human",
                               "no_human_need":END}
                               )



workflow = builder.compile()

