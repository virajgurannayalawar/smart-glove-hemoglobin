from pydantic import BaseModel


class GloveKeyResponse(BaseModel):
    glove_api_key: str


class GloveKeyRotateResponse(BaseModel):
    glove_api_key: str
