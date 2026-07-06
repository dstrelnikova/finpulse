from pydantic import BaseModel, ConfigDict, EmailStr, constr


class RegisterIn(BaseModel):
    name: constr(min_length=2, max_length=50)
    email: EmailStr
    password: constr(min_length=6)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Darya",
                "email": "darya@example.com",
                "password": "123456",
            }
        }
    )


class LoginIn(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
