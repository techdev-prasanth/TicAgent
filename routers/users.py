from fastapi import APIRouter , Depends
from db_config import get_session
from sqlalchemy.orm import Session
from utils.security import get_current_user
from models.auth_models import User

router = APIRouter(prefix="/users",tags=["users"])



@router.get("/")
def get_users(users : User = Depends(get_current_user), session : Session = Depends(get_session)):
    user = session.query(User).all()
    return user


