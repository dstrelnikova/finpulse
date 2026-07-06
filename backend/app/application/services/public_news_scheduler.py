import logging
import threading
from typing import Optional

from app.core.settings import settings
from app.infrastructure.dependencies import get_public_news_feed_use_case

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None


def start_public_news_scheduler() -> None:
    global _thread

    if not settings.NEWS_PUBLIC_AUTO_REFRESH_ENABLED:
        logger.info("Public news auto-refresh is disabled")
        return

    if _thread and _thread.is_alive():
        return

    _stop_event.clear()
    _thread = threading.Thread(target=_run_scheduler, name="public-news-daily-refresh", daemon=True)
    _thread.start()
    logger.info(
        "Public news auto-refresh scheduled every %s hour(s)",
        settings.NEWS_PUBLIC_AUTO_REFRESH_INTERVAL_HOURS,
    )


def stop_public_news_scheduler() -> None:
    _stop_event.set()


def _run_scheduler() -> None:
    startup_delay = settings.NEWS_PUBLIC_AUTO_REFRESH_STARTUP_DELAY_SEC
    interval_sec = settings.NEWS_PUBLIC_AUTO_REFRESH_INTERVAL_HOURS * 60 * 60

    if _stop_event.wait(startup_delay):
        return

    while not _stop_event.is_set():
        try:
            get_public_news_feed_use_case().refresh(force=False)
            logger.info("Public news auto-refresh completed")
        except Exception as exc:
            logger.warning("Public news auto-refresh failed: %s", exc)

        if _stop_event.wait(interval_sec):
            return
