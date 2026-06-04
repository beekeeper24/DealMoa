from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AIReviewRateLimitExceededException
from app.modules.ai_review.models import AIReviewUsageEvent

AIReviewTargetType = Literal["submission", "verified_review"]


class AIReviewUsageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def count_user_events_since(self, *, user_id: str, since: datetime) -> int:
        statement = select(func.count()).select_from(AIReviewUsageEvent).where(
            AIReviewUsageEvent.user_id == user_id,
            AIReviewUsageEvent.created_at >= since,
        )
        return int(self.session.scalar(statement) or 0)

    def create_event(
        self,
        *,
        user_id: str,
        target_type: AIReviewTargetType,
        now: datetime,
    ) -> AIReviewUsageEvent:
        event = AIReviewUsageEvent(
            user_id=user_id,
            target_type=target_type,
            created_at=now,
            updated_at=now,
        )
        self.session.add(event)
        self.session.flush()
        return event


class AIReviewRateLimiter:
    def __init__(
        self,
        *,
        repository: AIReviewUsageRepository,
        window_limit: int,
        window_hours: int,
    ) -> None:
        self.repository = repository
        self.window_limit = window_limit
        self.window_hours = window_hours

    def check_and_record(
        self,
        *,
        user_id: str,
        target_type: AIReviewTargetType,
        now: datetime,
    ) -> None:
        if self.window_limit <= 0:
            return

        since = now - timedelta(hours=self.window_hours)
        current_count = self.repository.count_user_events_since(user_id=user_id, since=since)
        if current_count >= self.window_limit:
            raise AIReviewRateLimitExceededException(
                limit=self.window_limit,
                window_hours=self.window_hours,
            )
        self.repository.create_event(user_id=user_id, target_type=target_type, now=now)
