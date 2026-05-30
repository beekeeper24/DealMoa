from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    ForbiddenException,
)
from app.modules.admin.models import AdminAuditLog
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import OfferStatusUpdateRequest
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.repository import ProductRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class OfferStatusUpdateResult:
    target_type: Literal["deal", "auction"]
    target_id: str
    previous_status: str
    status: str
    audit_log_id: str


class AdminUseCases:
    def __init__(
        self,
        *,
        admin_repository: AdminRepository,
        product_repository: ProductRepository,
        domain_events: DomainEventsUseCases,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.admin_repository = admin_repository
        self.product_repository = product_repository
        self.domain_events = domain_events
        self.now = now or utc_now

    def update_deal_status(
        self,
        *,
        actor: AuthenticatedUser,
        deal_id: str,
        request: OfferStatusUpdateRequest,
    ) -> OfferStatusUpdateResult:
        self._ensure_admin(actor)
        deal = self.product_repository.get_deal(deal_id)
        if deal is None:
            raise DealNotFoundException(deal_id)
        previous_status = deal.status
        now = self.now()
        deal.status = request.status
        deal.updated_at = now
        audit_log = self._record_audit_log(
            actor=actor,
            action="deal.status.changed",
            target_type="deal",
            target_id=deal.id,
            previous_status=previous_status,
            new_status=request.status,
            reason=request.reason,
            now=now,
        )
        self.domain_events.record_deal_status_changed(
            deal=deal,
            actor_user_id=actor.id,
            previous_status=previous_status,
            reason=request.reason,
        )
        return self._result(
            target_type="deal",
            target_id=deal.id,
            previous_status=previous_status,
            status=deal.status,
            audit_log_id=audit_log.id,
        )

    def update_auction_status(
        self,
        *,
        actor: AuthenticatedUser,
        auction_id: str,
        request: OfferStatusUpdateRequest,
    ) -> OfferStatusUpdateResult:
        self._ensure_admin(actor)
        auction = self.product_repository.get_auction(auction_id)
        if auction is None:
            raise AuctionNotFoundException(auction_id)
        previous_status = auction.status
        now = self.now()
        auction.status = request.status
        auction.updated_at = now
        audit_log = self._record_audit_log(
            actor=actor,
            action="auction.status.changed",
            target_type="auction",
            target_id=auction.id,
            previous_status=previous_status,
            new_status=request.status,
            reason=request.reason,
            now=now,
        )
        self.domain_events.record_auction_status_changed(
            auction=auction,
            actor_user_id=actor.id,
            previous_status=previous_status,
            reason=request.reason,
        )
        return self._result(
            target_type="auction",
            target_id=auction.id,
            previous_status=previous_status,
            status=auction.status,
            audit_log_id=audit_log.id,
        )

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()

    def _record_audit_log(
        self,
        *,
        actor: AuthenticatedUser,
        action: str,
        target_type: Literal["deal", "auction"],
        target_id: str,
        previous_status: str,
        new_status: str,
        reason: str | None,
        now: datetime,
    ) -> AdminAuditLog:
        return self.admin_repository.create_audit_log(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                previous_status=previous_status,
                new_status=new_status,
                reason=reason,
                created_at=now,
                updated_at=now,
            )
        )

    def _result(
        self,
        *,
        target_type: Literal["deal", "auction"],
        target_id: str,
        previous_status: str,
        status: str,
        audit_log_id: str,
    ) -> OfferStatusUpdateResult:
        return OfferStatusUpdateResult(
            target_type=target_type,
            target_id=target_id,
            previous_status=previous_status,
            status=status,
            audit_log_id=audit_log_id,
        )
