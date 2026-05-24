from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.products.models import Auction, Deal, Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_product(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product

    def get_product(self, product_id: str) -> Product | None:
        return self.session.get(Product, product_id)

    def list_products(self) -> list[Product]:
        return list(self.session.scalars(select(Product).order_by(Product.created_at.desc())))

    def create_deal(self, deal: Deal) -> Deal:
        self.session.add(deal)
        self.session.flush()
        return deal

    def list_deals_for_product(self, product_id: str) -> list[Deal]:
        return list(
            self.session.scalars(
                select(Deal).where(Deal.product_id == product_id).order_by(Deal.created_at.desc())
            )
        )

    def create_auction(self, auction: Auction) -> Auction:
        self.session.add(auction)
        self.session.flush()
        return auction

    def list_auctions_for_product(self, product_id: str) -> list[Auction]:
        return list(
            self.session.scalars(
                select(Auction)
                .where(Auction.product_id == product_id)
                .order_by(Auction.created_at.desc())
            )
        )
