from pydantic import BaseModel, EmailStr, constr
from auth.constants import ValidRoles
from typing import Optional


class UserBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    email: EmailStr
    role: str

    def validate_role(self):
        VALID_ROLES = ValidRoles.values()
        if self.role not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserResponse(UserBase):
    id: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None