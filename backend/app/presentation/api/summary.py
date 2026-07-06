from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.summarize_article import GetNewsFeed
from app.infrastructure.database.user_repo_impl import UserRepositorySQL
from app.infrastructure.dependencies import get_news_feed_use_case, get_user_repo
from app.infrastructure.security.auth_jwt import get_current_user
from app.infrastructure.security.authz import require_permissions
from app.presentation.schemas.summary import NewsBlockOut, NewsIndicatorOut

router = APIRouter(prefix="/news", tags=["News"])


def to_news_block_out(b) -> NewsBlockOut:
    return NewsBlockOut(
        id=b.id,
        slug=b.slug,
        title=b.title,
        source=b.source,
        url=b.url,
        summary=b.summary,
        bullets=b.bullets,
        conclusion=b.conclusion,
        risks=b.risks,
        indicator=(
            NewsIndicatorOut(
                impact=b.indicator.impact,
                confidence=b.indicator.confidence,
                rationale=b.indicator.rationale,
            )
            if b.indicator is not None
            else None
        ),
        asof=b.asof,
    )


@router.get("/feed", response_model=List[NewsBlockOut], dependencies=[Depends(require_permissions(["news:list"]))])
async def get_personal_news_feed(
    force: bool = False,
    current_user=Depends(get_current_user),
    user_repo: UserRepositorySQL = Depends(get_user_repo),
    use_case: GetNewsFeed = Depends(get_news_feed_use_case),
):
    user = user_repo.get_by_email(current_user.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    blocks = await use_case.execute_async(user, force=force)
    return [to_news_block_out(b) for b in blocks]


@router.get(
    "/{news_id}",
    response_model=NewsBlockOut,
    dependencies=[Depends(require_permissions(["news:list"]))],
)
async def get_news_item(
    news_id: str,
    force: bool = False,
    current_user=Depends(get_current_user),
    user_repo: UserRepositorySQL = Depends(get_user_repo),
    use_case: GetNewsFeed = Depends(get_news_feed_use_case),
):
    user = user_repo.get_by_email(current_user.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    blocks = await use_case.execute_async(user, force=force)

    news_item = next((b for b in blocks if b.id == news_id), None)
    if not news_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")

    return to_news_block_out(news_item)
