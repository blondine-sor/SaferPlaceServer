from fastapi import FastAPI,File,UploadFile,Form
from fastapi.middleware.cors import CORSMiddleware
import snowflake.connector as sc
import uvicorn
from dotenv import load_dotenv
import os
import sys
from models import User,E_Contacts
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









if __name__ == "__name__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)

