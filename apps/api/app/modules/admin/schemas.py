from typing import Literal

from pydantic import BaseModel, Field

OfferStatus = Literal["pending", "active", "verified", "rejected", "blocked", "closed"]


class OfferStatusUpdateRequest(BaseModel):
    status: OfferStatus
    reason: str | None = Field(default=None, max_length=1000)


class OfferStatusUpdateResponse(BaseModel):
    target_type: Literal["deal", "auction"] = Field(alias="targetType")
    target_id: str = Field(alias="targetId")
    previous_status: str = Field(alias="previousStatus")
    status: str
    audit_log_id: str = Field(alias="auditLogId")
