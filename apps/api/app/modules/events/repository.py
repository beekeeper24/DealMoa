from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.events.models import DomainEvent


class DomainEventsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(self, event: DomainEvent) -> DomainEvent:
        self.session.add(event)
        self.session.flush()
        return event

    def list_unpublished(self, *, limit: int) -> list[DomainEvent]:
        statement = (
            select(DomainEvent)
            .where(DomainEvent.published_at.is_(None))
            .order_by(DomainEvent.created_at, DomainEvent.id)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def mark_published(self, *, event_id: str, published_at: datetime) -> None:
        statement = (
            update(DomainEvent)
            .where(DomainEvent.id == event_id)
            .values(published_at=published_at, updated_at=published_at)
        )
        self.session.execute(statement)
        self.session.flush()
