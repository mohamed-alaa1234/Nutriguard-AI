from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def authenticate_user(
    db: Session, email: str, password: str
) -> models.User | None:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=schemas.UserRead, status_code=201)
def register(
    registration: schemas.RegistrationData,
    db: Session = Depends(get_db),
):
    print("[DEBUG] /api/v1/auth/register payload:", registration.dict())
    existing = (
        db.query(models.User)
        .filter(models.User.email == registration.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    full_name = f"{registration.first_name} {registration.last_name}".strip()
    hashed_password = get_password_hash(registration.password)

    user = models.User(
        email=registration.email,
        full_name=full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print("[DEBUG] /api/v1/auth/register created user id:", user.id)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    print("[DEBUG] /api/v1/auth/login username:", form_data.username)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    print("[DEBUG] /api/v1/auth/login issued token for user id:", user.id)
    return schemas.Token(access_token=access_token)

