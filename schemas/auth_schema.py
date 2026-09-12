from pydantic import (BaseModel ,
                    EmailStr ,
                    Field ,
                    field_validator ,
                    model_validator ,
                    ConfigDict
)

from typing import List , Optional


class AccountCreation(BaseModel):
    full_name : str = Field(max_length=20, min_length=2)
    email : EmailStr
    username : str 
    password : str = Field(min_length=8,max_length=16,description="users password")
    confirm_password : str = Field(min_length=8,max_length=16,description="users confirm password")

    @model_validator(mode="after")
    def check_password(self):
        print("  ")
        print(self)
        print("  ")
        if self.password != self.confirm_password:
            raise ValueError("confirm password does not match")
        return self


class UserLogin(BaseModel):
    email : EmailStr
    password : str = Field(min_length=8,max_length=16,description="users password")

class UserDetails(BaseModel):
    id : int
    username : Optional[str] = None
    email : EmailStr
    full_name : str

    model_config = ConfigDict(from_attributes=True)


class CheckAge(BaseModel):
    age : int