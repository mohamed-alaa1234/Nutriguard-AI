from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class RegistrationData(BaseModel):
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    email: EmailStr
    password: constr(min_length=8)
    account_type: constr(min_length=1)


class AnalyzeRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    chronic_disease: constr(min_length=1)


class AnalyzeResponse(BaseModel):
    bmi: float
    bmi_status: str
    daily_calories: int
    recommended_foods: list[str]
    forbidden_foods: list[str]
    health_habits: list[str]
    risk_level: str
    message: str


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None

