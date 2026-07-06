from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.presentation.schemas.summary import NewsBlockOut
from app.infrastructure.dependencies import (
    get_public_news_feed_use_case,
    get_public_news_item_use_case,
    get_public_news_item_by_slug_use_case,
)
from app.application.use_cases.public_news.public_news import (
    GetPublicNewsFeed,
    GetPublicNewsItem,
    GetPublicNewsItemBySlug,
)

router = APIRouter(prefix="/public/news", tags=["Public News"])


@router.get("", response_model=List[NewsBlockOut])
def get_public_news_feed(
    limit: int = 50,
    force: bool = False,
    use_case: GetPublicNewsFeed = Depends(get_public_news_feed_use_case),
):
    limit = max(1, min(limit, 100))
    return use_case.execute(limit=limit, force=force)


@router.get("/slug/{slug}", response_model=NewsBlockOut)
def get_public_news_item_by_slug(
    slug: str,
    use_case: GetPublicNewsItemBySlug = Depends(get_public_news_item_by_slug_use_case),
):
    item = use_case.execute(slug=slug)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")
    return item


@router.get("/{news_id}", response_model=NewsBlockOut)
def get_public_news_item(
    news_id: int,
    use_case: GetPublicNewsItem = Depends(get_public_news_item_use_case),
):
    item = use_case.execute(news_id=news_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")
    return item
