from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import (
    DiscussionCommentNotFoundException,
    ForbiddenException,
    ProductNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.discussions.models import ProductDiscussionComment
from app.modules.discussions.repository import DiscussionsRepository
from app.modules.discussions.schemas import (
    DiscussionCreateRequest,
    DiscussionModerationRequest,
)
from app.modules.products.repository import ProductRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


class DiscussionsUseCases:
    def __init__(
        self,
        *,
        repository: DiscussionsRepository,
        product_repository: ProductRepository,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.product_repository = product_repository
        self.now = now or utc_now

    def create_comment(
        self,
        *,
        actor: AuthenticatedUser,
        product_id: str,
        request: DiscussionCreateRequest,
    ) -> ProductDiscussionComment:
        self._ensure_product_exists(product_id)
        now = self.now()
        return self.repository.create_comment(
            ProductDiscussionComment(
                product_id=product_id,
                user_id=actor.id,
                body=request.body,
                status="visible",
                created_at=now,
                updated_at=now,
            )
        )

    def list_public_comments(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductDiscussionComment]:
        self._ensure_product_exists(product_id)
        return self.repository.list_public_comments(
            product_id=product_id,
            limit=limit,
            cursor=cursor,
        )

    def list_admin_comments(
        self,
        *,
        actor: AuthenticatedUser,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductDiscussionComment]:
        self._ensure_admin(actor)
        return self.repository.list_admin_comments(status=status, limit=limit, cursor=cursor)

    def moderate_comment(
        self,
        *,
        actor: AuthenticatedUser,
        comment_id: str,
        request: DiscussionModerationRequest,
    ) -> ProductDiscussionComment:
        self._ensure_admin(actor)
        comment = self.repository.get_comment(comment_id)
        if comment is None:
            raise DiscussionCommentNotFoundException(comment_id)

        now = self.now()
        previous_status = comment.status
        if request.action == "hide":
            comment.status = "hidden"
            action = "discussion_comment.hidden"
        else:
            comment.status = "visible"
            action = "discussion_comment.restored"
        comment.moderated_by_user_id = actor.id
        comment.moderation_note = request.moderation_note
        comment.moderated_at = now
        comment.updated_at = now
        self.repository.create_audit_log(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type="discussion_comment",
                target_id=comment.id,
                previous_status=previous_status,
                new_status=comment.status,
                reason=request.moderation_note,
                created_at=now,
                updated_at=now,
            )
        )
        return comment

    def _ensure_product_exists(self, product_id: str) -> None:
        if self.product_repository.get_product(product_id) is None:
            raise ProductNotFoundException(product_id)

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()
