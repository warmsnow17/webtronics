import os

import requests
from fastapi import HTTPException, Depends, status, APIRouter, Body
from datetime import timedelta
from sqlalchemy.orm import Session

from app.schemas import schemas
from app.models.user import User
from app.models.database import get_db
from app.services.auth import (
    get_user,
    verify_password,
    create_access_token,
    get_current_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES,
)


from dotenv import load_dotenv

from app.services.requests_db import get_user_by_email

load_dotenv()


router = APIRouter()


@router.post("/login", response_model=schemas.Token)
async def login(username: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    """
    Войти в систему с использованием имени пользователя и пароля

    - **username**: Имя пользователя
    - **password**: Пароль пользователя
    """
    user = get_user(db, username=username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/create_user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создать нового пользователя

    - **username**: Имя нового пользователя
    - **password**: Пароль нового пользователя
    - **email**: Email нового пользователя (не обязательно)
    """
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    if user.email:
        db_user = get_user_by_email(db, user_email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already in use")

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    if user.email:
        response = requests.get(f'https://person.clearbit.com/v2/combined/find?email={user.email}',
                                headers={'Authorization': f'Bearer {os.getenv("CLEARBIT_API_KEY")}'})
        if response.status_code == 200:
            external_data = response.json()
            db_user.external_data = external_data
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    """
    Получить информацию о текущем пользователе
    """
    return current_user


@router.get("/users/{user_id}", response_model=schemas.User)
def get_current_use_by_id(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получить информацию о пользователе по id
    """
    db_user = get_user(db, str(current_user.username))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
