from pydantic import BaseModel


class GloveKeyResponse(BaseModel):
    GloveApiKey: str


class GloveKeyRotateResponse(BaseModel):
    GloveApiKey: str
