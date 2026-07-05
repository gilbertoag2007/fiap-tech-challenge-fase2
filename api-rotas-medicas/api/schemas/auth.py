from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: str = Field(..., min_length=1, max_length=100)
    senha: str = Field(..., min_length=1, max_length=200)


class LoginResponse(BaseModel):
    token: str
    expires_in: int
