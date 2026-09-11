from fastapi import FastAPI , APIRouter , Depends , HTTPException
from utils.security import (hash_password,
                            verify_password ,
                            OAuth2PasswordRequestForm ,
                            OAuth2PasswordBearer,
                            create_access_token,
                            create_refresh_token,
                            get_current_user)

from models.auth_models import User
from schemas.auth_schema import (
      AccountCreation,
      UserLogin,
      UserDetails)
from sqlalchemy.orm import Session
from db_config import Base , engine , local_session , get_session
from fastapi.responses import JSONResponse 
from fastapi import status
from dotenv import load_dotenv

from typing import List



load_dotenv()


router = APIRouter(prefix="/auth",tags=["auth"])

@router.get("/users/",response_model=List[UserDetails])
def get_users(user : User=Depends(get_current_user),
               db : Session = Depends(get_session)):
    users = db.query(User).all()
    return users


@router.post("/signup/")
def create_account(request:AccountCreation,db : Session=Depends(get_session)):

    existing_user = db.query(User).filter(User.email==request.email).first()
    if existing_user:
        return HTTPException(detail="Account exist already",status_code=status.HTTP_400_BAD_REQUEST)
    user = User(
            full_name=request.full_name,
            email=request.email,
            password=hash_password(request.password),
            username=request.username
        )
    try:
            db.add(user) # stores in the session
            db.commit() # stores in the db after session
            db.refresh(user)
            return JSONResponse(
                  content={"messages":"Account has been created"},
                  status_code=status.HTTP_201_CREATED)
    except Exception as e:
            return JSONResponse(
                  content={"messages":"Account has not been created"},
                  status_code=status.HTTP_400_BAD_REQUEST
                  )



@router.post("/login/")
def user_login(request: OAuth2PasswordRequestForm = Depends() , db : Session = Depends(get_session)):

    check_user = db.query(User).filter(User.username==request.username).first()

    if check_user is None:
   
        return HTTPException(detail="email or password is incorrect",status_code=status.HTTP_400_BAD_REQUEST)

    if not verify_password(request.password,check_user.password):
      
        return HTTPException(detail="email or password is incorrect",status_code=status.HTTP_400_BAD_REQUEST)


    access_token = create_access_token({"sub":check_user.email})
    referesh_token = create_refresh_token({"sub":check_user.email})

    return JSONResponse(content={"access":access_token,"message":"login successfull"},status_code=status.HTTP_200_OK)


