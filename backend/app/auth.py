from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from .database import users_collection

from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from .database import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


class UserAuth(BaseModel):
    email: str
    password: str


def hash_password(password: str):
    return pwd_context.hash(password[:72])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/signup")
async def signup(user: UserAuth):
    email = user.email
    password = user.password


    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    existing = await users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(password)

    await users_collection.insert_one({
        "email": email,
        "password": hashed
    })
    await users_collection.insert_one({"email": email, "password": hashed})

    return {"message": "User created successfully"}


@router.post("/login")
async def login(user: UserAuth):
    email = user.email
    password = user.password

    db_user = users_collection.find_one({"email": email})
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": email})

    return {"access_token": token, "token_type": "bearer"}