from pydantic import BaseModel
from typing import Optional

class OAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None

class OAuthUserInfo(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None

class OAuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    is_new_user: bool = False

class OAuthProvider(BaseModel):
    name: str
    display_name: str
    authorization_url: str