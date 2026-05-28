from dataclasses import dataclass
from datetime import UTC, datetime

from app.main import create_app
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.products.router import get_product_use_cases
from app.modules.products.schemas import AuctionBidCreateRequest, AuctionBidResponse
from fastapi.testclient import TestClient

NOW = datetime(2026, 5, 29, 9, 0, tzinfo=UTC)


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
class FakeProductUseCases:
    placed_bid: tuple[str, str, int] | None = None

    def place_auction_bid(
        self,
        *,
        user_id: str,
        auction_id: str,
        request: AuctionBidCreateRequest,
    ) -> AuctionBidResponse:
        amount = request.amount
        self.placed_bid = (user_id, auction_id, amount)
        return AuctionBidResponse(
            id="bid-1",
            auctionId=auction_id,
            userId=user_id,
            amount=amount,
            createdAt=NOW,
        )


def make_client(use_cases: FakeProductUseCases) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_use_cases] = lambda: FakeAuthUseCases()
    app.dependency_overrides[get_product_use_cases] = lambda: use_cases
    return TestClient(app)


def test_place_auction_bid_requires_bearer_token() -> None:
    client = make_client(FakeProductUseCases())

    response = client.post("/api/v1/auctions/auction-1/bids", json={"amount": 750000})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_place_auction_bid_uses_current_user() -> None:
    use_cases = FakeProductUseCases()
    client = make_client(use_cases)

    response = client.post(
        "/api/v1/auctions/auction-1/bids",
        json={"amount": 750000},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "bid-1",
        "auctionId": "auction-1",
        "userId": "user-1",
        "amount": 750000,
        "createdAt": "2026-05-29T09:00:00Z",
    }
    assert use_cases.placed_bid == ("user-1", "auction-1", 750000)
