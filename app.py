from fastapi import Depends, FastAPI,File, HTTPException,UploadFile,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import snowflake.connector as sc
import uvicorn
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import sys
from models import User,E_Contacts,UserLogin
from functions import password_hash,password_verify


load_dotenv()
# Create a FastAPI instance
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#connexion to snowflake
conn = sc.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    database=os.getenv("SNOWFLAKE_DATABASE")
)
# Create a cursor object
cur = conn.cursor()

#JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#request to get user
def get_user(email: str, password: str):
    # verify if the user exists
    cur.execute(f"SELECT PASSWORD FROM SAFERPLACES.USERS.USER WHERE EMAIL='{email}'")
    password_db = cur.fetchone()
    if password_db and password_verify(password, password_db[0]):
        cur.execute(f"SELECT * FROM SAFERPLACES.USERS.USER WHERE EMAIL='{email}'")
    user = cur.fetchone()
    return user

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(email=email)
    if user is None:
        raise credentials_exception
    return








#request to add a user

@app.post("/add_user")
async def add_user(user: User):
    #verifier si l'utilisateur existe
    cur.execute(f"SELECT * FROM SAFERPLACES.USERS.USER WHERE EMAIL='{user.email}'")
    if cur.fetchone():
        return {"status": "user already exists"}
    else:
        #add user
        password_hashed = password_hash(user.password)
        cur.execute(
            f"INSERT INTO SAFERPLACES.USERS.USER (NAME,EMAIL,PASSWORD,PHONE,AUTHORIZATION) VALUES ('{user.name}','{user.email}','{password_hashed}','{user.phone}','{user.authorization}')"
        )
        cur.execute("commit")
        return {"status": "user added"}
    

#request to add an emergency contact
@app.post("/add_emergency_contact")
async def add_emergency_contact(e_contact: E_Contacts):
        cur.execute(
            f"INSERT INTO SAFERPLACES.USERS.E_CONTACTS (USER_ID,NAME,PHONE,NIVEAU) VALUES ('{e_contact.user_id}','{e_contact.name}','{e_contact.phone}','{e_contact.niveau}')"
        )
        cur.execute("commit")
        return {"status": "contact added"}

#request for user login
@app.post("/login")
# function returns token user information token type and token expiration
async def login(user: UserLogin):
    user_db = get_user(user.email, user.password)
    if user_db:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_db[1]}, expires_delta=access_token_expires
        )
        user_info = {
            "id": user_db[0],
            "name": user_db[1],
            "email": user_db[2],
            "phone": user_db[4],
            "authorization": user_db[5],
            "is_active": True
        }
        return {"access_token": access_token, "user":user_info, "token_type": "bearer", "expires": access_token_expires}
    else:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
     
     
     

#creating a protected route
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user






if __name__ == "__name__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)

