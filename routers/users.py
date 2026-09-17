from fastapi import APIRouter , Depends
from db_config import get_session
from sqlalchemy.orm import Session
from utils.security import get_current_user
from models.auth_models import User
from schemas.auth_schema import UserDetails
from typing import List
router = APIRouter(prefix="/api/v1/users",tags=["users"])
import uuid
from fastapi import status
from fastapi.responses  import JSONResponse



@router.get("/",response_model=List[UserDetails])
async def get_users(users : User = Depends(get_current_user), 
              session : Session = Depends(get_session),
              limit : int = 100,
              offset : int = 0):
    users = session.query(User).order_by(User.created_at.desc()
                                         ).limit(limit).offset(offset)
    return  users

