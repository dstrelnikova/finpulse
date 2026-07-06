from fastapi import Depends
from fastapi.params import Depends as DependsParam

from app.application.interfaces.user import IUserRepository
from app.application.use_cases.chat.chat_with_llm import ChatWithLLM
from app.application.use_cases.summarize_article import GetNewsFeed
from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.chat_repo_impl import ChatRepositorySQL
from app.infrastructure.database.chat_session_repo_impl import ChatSessionRepositorySQL
from app.infrastructure.database.news_cache_repo_impl import NewsCacheRepoSQL
from app.infrastructure.database.user_repo_impl import UserRepositorySQL
from app.application.interfaces.llm import ILLMService
from app.infrastructure.llm.gigachat_llm_service import GigaChatLLMService
from app.infrastructure.llm.ollama_llm_service import OllamaLLMService
from app.infrastructure.llm.scraper_service import ScraperService
from app.infrastructure.news.rss_service import RssNewsService
from app.application.use_cases.public_news.public_news import (
    GetPublicNewsFeed,
    GetPublicNewsItem,
    GetPublicNewsItemBySlug,
)
from app.infrastructure.database.news_repo_impl import NewsRepositorySQL
from app.infrastructure.moex.moex_service import MoexService


def get_user_repo() -> IUserRepository:
    return UserRepositorySQL(SessionLocal)


def get_scraper() -> ScraperService:
    return ScraperService()


def get_rss_news_service() -> RssNewsService:
    return RssNewsService()


def get_news_cache_repo() -> NewsCacheRepoSQL:
    return NewsCacheRepoSQL()


def get_news_llm_service() -> ILLMService:
    return GigaChatLLMService()


def get_chat_llm_service() -> ILLMService:
    return OllamaLLMService()


def get_chat_repo() -> ChatRepositorySQL:
    return ChatRepositorySQL()


def get_chat_session_repo() -> ChatSessionRepositorySQL:
    return ChatSessionRepositorySQL()


def get_chat_use_case(
    llm: ILLMService = Depends(get_chat_llm_service),
    repo: ChatRepositorySQL = Depends(get_chat_repo),
) -> ChatWithLLM:
    return ChatWithLLM(llm=llm, chat_repo=repo)


def get_news_repo() -> NewsRepositorySQL:
    return NewsRepositorySQL()


def get_moex_service() -> MoexService:
    return MoexService()


def get_news_feed_use_case(
    scraper: ScraperService = Depends(get_scraper),
    llm=Depends(get_news_llm_service),
    cache_repo: NewsCacheRepoSQL = Depends(get_news_cache_repo),
    news_repo: NewsRepositorySQL = Depends(get_news_repo),
    rss: RssNewsService = Depends(get_rss_news_service),
) -> GetNewsFeed:
    if isinstance(scraper, DependsParam):
        scraper = get_scraper()
    if isinstance(llm, DependsParam):
        llm = get_news_llm_service()
    if isinstance(cache_repo, DependsParam):
        cache_repo = get_news_cache_repo()
    if isinstance(news_repo, DependsParam):
        news_repo = get_news_repo()
    if isinstance(rss, DependsParam):
        rss = get_rss_news_service()
    return GetNewsFeed(scraper=scraper, llm=llm, cache_repo=cache_repo, news_repo=news_repo, rss=rss)


def get_public_news_feed_use_case(
    repo: NewsRepositorySQL = Depends(get_news_repo),
    rss: RssNewsService = Depends(get_rss_news_service),
    generator: GetNewsFeed = Depends(get_news_feed_use_case),
) -> GetPublicNewsFeed:
    if isinstance(repo, DependsParam):
        repo = get_news_repo()
    if isinstance(rss, DependsParam):
        rss = get_rss_news_service()
    if isinstance(generator, DependsParam):
        generator = get_news_feed_use_case()
    return GetPublicNewsFeed(repo, rss, generator)


def get_public_news_item_use_case(repo: NewsRepositorySQL = Depends(get_news_repo)) -> GetPublicNewsItem:
    return GetPublicNewsItem(repo)


def get_public_news_item_by_slug_use_case(
    repo: NewsRepositorySQL = Depends(get_news_repo),
) -> GetPublicNewsItemBySlug:
    return GetPublicNewsItemBySlug(repo)
