from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    authorization: str


class E_Contacts(BaseModel):
    user_id: int
    name: str
    phone: str
    niveau: str

class UserLogin(BaseModel):
    email: str
    password: str   

class Contacts(BaseModel):
    user_id: int
    