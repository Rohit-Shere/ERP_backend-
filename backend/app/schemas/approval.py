from pydantic import BaseModel, Field


class ApprovalDecision(BaseModel):
    comments: str | None = Field(default=None, max_length=2000)