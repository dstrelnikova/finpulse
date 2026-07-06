from fastapi import APIRouter, Depends

from app.infrastructure.dependencies import get_moex_service
from app.infrastructure.moex.moex_service import MoexService
from app.presentation.schemas.moex import MoexQuotesResponse

router = APIRouter(prefix="/public/moex", tags=["Public MOEX"])


@router.get("/imoex/quotes", response_model=MoexQuotesResponse)
def get_imoex_quotes(
    limit: int = 12,
    moex: MoexService = Depends(get_moex_service),
):
    safe_limit = max(1, min(limit, 20))
    return moex.get_imoex_quotes(limit=safe_limit)
