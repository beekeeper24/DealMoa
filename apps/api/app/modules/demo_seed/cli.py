import argparse
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.session import create_session_factory
from app.modules.demo_seed.use_cases import seed_korean_demo_data
from app.modules.products.repository import ProductRepository
from app.modules.search.client import ElasticsearchSearchClient
from app.modules.search.use_cases import SearchClient, SearchUseCases


def run_demo_seed(
    *,
    session_factory: sessionmaker[Session],
    reindex: bool,
    search_client: SearchClient | None = None,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    session = session_factory()
    try:
        seed_summary = seed_korean_demo_data(session, now=now)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    reindex_summary = None
    if reindex:
        session = session_factory()
        try:
            if search_client is None:
                search_client = ElasticsearchSearchClient(get_settings().elasticsearch_url)
            reindex_summary = SearchUseCases(
                ProductRepository(session),
                search_client,
                now=now,
            ).rebuild_indexes()
        finally:
            session.close()

    return {
        "seed": seed_summary.to_dict(),
        "reindex": reindex_summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Korean DealMoa demo data.")
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Rebuild Elasticsearch search indexes after seeding.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL. Defaults to app settings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    session_factory = create_session_factory(args.database_url or settings.database_url)
    result = run_demo_seed(
        session_factory=session_factory,
        reindex=args.reindex,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
