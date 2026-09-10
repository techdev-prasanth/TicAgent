from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from jose import JWTError , jwt
from datetime import datetime , timezone , timedelta
from fastapi import Depends , HTTPException
from sqlalchemy.orm import Session
from db_config import get_session
from models.auth_models import User

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7



password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password,hased_password):
    return password_hash.verify(plain_password,hased_password)

def hash_password(password: str) -> str:
    return password_hash.hash(password)



def create_access_token(data : dict):

    payload = data.copy()

    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)



def create_refresh_token(data : dict):

    payload = data.copy()

    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload["type"] = "referesh"

    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM) 



def get_current_user(token : str = Depends(oauth2_scheme),
                      db : Session = Depends(get_session)):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(detail="Invalid credentials")

    except JWTError:
        raise HTTPException(detail="Invalid credentials")


    user = db.query(User).filter(User.email==email).first()

    if user is None:
        raise HTTPException(detail="Invalid credentials")


    return user