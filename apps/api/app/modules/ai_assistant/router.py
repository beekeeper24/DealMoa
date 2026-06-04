from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.modules.ai_assistant.factory import create_ai_assistant_provider
from app.modules.ai_assistant.schemas import (
    AiSearchRequest,
    AiSearchResponse,
    ProductPurchaseCheckResponse,
)
from app.modules.ai_assistant.use_cases import AiAssistantUseCases
from app.modules.evidence.repository import EvidenceRepository
from app.modules.products.repository import ProductRepository
from app.modules.search.client import ElasticsearchSearchClient
from app.modules.search.use_cases import SearchUseCases

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


def get_ai_assistant_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> AiAssistantUseCases:
    settings = get_settings()
    product_repository = ProductRepository(session)
    return AiAssistantUseCases(
        search_use_cases=SearchUseCases(
            product_repository,
            ElasticsearchSearchClient(settings.elasticsearch_url),
        ),
        product_repository=product_repository,
        evidence_repository=EvidenceRepository(session),
        ai_assistant_provider=create_ai_assistant_provider(settings),
    )


@router.post("/search", response_model=AiSearchResponse, response_model_exclude_none=True)
def search_with_ai_assistant(
    request: AiSearchRequest,
    use_cases: Annotated[AiAssistantUseCases, Depends(get_ai_assistant_use_cases)],
) -> AiSearchResponse:
    return use_cases.search(request)


@router.get(
    "/products/{product_id}/purchase-check",
    response_model=ProductPurchaseCheckResponse,
    response_model_exclude_none=True,
)
def check_product_purchase(
    product_id: str,
    use_cases: Annotated[AiAssistantUseCases, Depends(get_ai_assistant_use_cases)],
) -> ProductPurchaseCheckResponse:
    return use_cases.purchase_check(product_id)
