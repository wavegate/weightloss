from pydantic import BaseModel, Field


class MeetupSyncRequest(BaseModel):
    location: str = Field(default="cupertino", min_length=1, max_length=64)
    keywords: str = Field(default="", max_length=256)


class MeetupSyncProgress(BaseModel):
    type: str
    page: int = 0
    fetched: int = 0
    saved: int = 0
    skipped: int = 0
    message: str | None = None
