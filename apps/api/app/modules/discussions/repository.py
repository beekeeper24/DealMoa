from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.discussions.models import ProductDiscussionComment

DiscussionT = TypeVar("DiscussionT", bound=ProductDiscussionComment)


class DiscussionsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_comment(self, comment: ProductDiscussionComment) -> ProductDiscussionComment:
        self.session.add(comment)
        self.session.flush()
        self.session.refresh(comment, attribute_names=["user"])
        return comment

    def get_comment(self, comment_id: str) -> ProductDiscussionComment | None:
        statement = (
            select(ProductDiscussionComment)
            .options(joinedload(ProductDiscussionComment.user))
            .where(ProductDiscussionComment.id == comment_id)
        )
        return self.session.scalar(statement)

    def list_public_comments(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductDiscussionComment]:
        statement = (
            select(ProductDiscussionComment)
            .options(joinedload(ProductDiscussionComment.user))
            .where(
                ProductDiscussionComment.product_id == product_id,
                ProductDiscussionComment.status == "visible",
            )
            .order_by(
                ProductDiscussionComment.created_at.desc(),
                ProductDiscussionComment.id.desc(),
            )
        )
        if cursor is not None:
            cursor_item = self.session.get(ProductDiscussionComment, cursor)
            if (
                cursor_item is None
                or cursor_item.product_id != product_id
                or cursor_item.status != "visible"
            ):
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def list_admin_comments(
        self,
        *,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductDiscussionComment]:
        statement = (
            select(ProductDiscussionComment)
            .options(joinedload(ProductDiscussionComment.user))
            .where(ProductDiscussionComment.status == status)
            .order_by(
                ProductDiscussionComment.created_at.desc(),
                ProductDiscussionComment.id.desc(),
            )
        )
        if cursor is not None:
            cursor_item = self.session.get(ProductDiscussionComment, cursor)
            if cursor_item is None or cursor_item.status != status:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def create_audit_log(self, audit_log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(audit_log)
        self.session.flush()
        return audit_log

    def _page(
        self,
        statement: Select[tuple[DiscussionT]],
        limit: int,
    ) -> CursorPage[DiscussionT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[ProductDiscussionComment]],
        cursor_item: ProductDiscussionComment,
    ) -> Select[tuple[ProductDiscussionComment]]:
        return statement.where(
            or_(
                ProductDiscussionComment.created_at < cursor_item.created_at,
                and_(
                    ProductDiscussionComment.created_at == cursor_item.created_at,
                    ProductDiscussionComment.id < cursor_item.id,
                ),
            )
        )
