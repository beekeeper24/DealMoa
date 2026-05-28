from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.pagination import CursorPage
from app.main import create_app
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.notifications.router import get_notifications_use_cases
from app.modules.notifications.schemas import NotificationResponse
from fastapi.testclient import TestClient

NOW = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)


@dataclass
class FakeAuthUseCases:
    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="user-1",
            email="user@example.com",
            nickname="Deal User",
            role="USER",
        )


@dataclass
class FakeNotificationsUseCases:
    listed_for: tuple[str, int, str | None, bool] | None = None
    counted_for: str | None = None
    marked_read: tuple[str, str] | None = None
    marked_all_read_for: str | None = None

    def list_notifications(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
        unread_only: bool = False,
    ) -> CursorPage[NotificationResponse]:
        self.listed_for = (user_id, limit, cursor, unread_only)
        return CursorPage(
            items=[
                NotificationResponse(
                    id="notification-1",
                    type="new_deal",
                    title="새 핫딜",
                    body="관심 상품에 새 핫딜이 있습니다.",
                    targetType="product",
                    targetId="product-1",
                    metadata={"source": "test"},
                    readAt=None,
                    createdAt=NOW,
                )
            ],
            next_cursor=None,
        )

    def count_unread(self, *, user_id: str) -> int:
        self.counted_for = user_id
        return 3

    def mark_read(self, *, user_id: str, notification_id: str) -> NotificationResponse:
        self.marked_read = (user_id, notification_id)
        return NotificationResponse(
            id=notification_id,
            type="new_deal",
            title="새 핫딜",
            body="관심 상품에 새 핫딜이 있습니다.",
            targetType="product",
            targetId="product-1",
            metadata={},
            readAt=NOW,
            createdAt=NOW,
        )

    def mark_all_read(self, *, user_id: str) -> int:
        self.marked_all_read_for = user_id
        return 2


def make_client(use_cases: FakeNotificationsUseCases) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_use_cases] = lambda: FakeAuthUseCases()
    app.dependency_overrides[get_notifications_use_cases] = lambda: use_cases
    return TestClient(app)


def test_list_notifications_requires_bearer_token() -> None:
    client = make_client(FakeNotificationsUseCases())

    response = client.get("/api/v1/notifications")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_list_notifications_uses_current_user_and_filters() -> None:
    use_cases = FakeNotificationsUseCases()
    client = make_client(use_cases)

    response = client.get(
        "/api/v1/notifications",
        params={"limit": 10, "cursor": "cursor-1", "unreadOnly": True},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "notification-1"
    assert response.json()["items"][0]["readAt"] is None
    assert use_cases.listed_for == ("user-1", 10, "cursor-1", True)


def test_unread_count_uses_current_user() -> None:
    use_cases = FakeNotificationsUseCases()
    client = make_client(use_cases)

    response = client.get(
        "/api/v1/notifications/unread-count",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"count": 3}
    assert use_cases.counted_for == "user-1"


def test_mark_read_uses_current_user() -> None:
    use_cases = FakeNotificationsUseCases()
    client = make_client(use_cases)

    response = client.post(
        "/api/v1/notifications/notification-1/read",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json()["readAt"] == "2026-05-28T12:00:00Z"
    assert use_cases.marked_read == ("user-1", "notification-1")


def test_mark_all_read_uses_current_user() -> None:
    use_cases = FakeNotificationsUseCases()
    client = make_client(use_cases)

    response = client.post(
        "/api/v1/notifications/read-all",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"updatedCount": 2}
    assert use_cases.marked_all_read_for == "user-1"
