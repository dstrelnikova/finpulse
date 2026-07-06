import json
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models import News
from app.infrastructure.utils import slugify
from app.presentation.schemas.summary import NewsBlockOut, NewsIndicatorOut

_GENERIC_ANALYSIS_MARKERS = (
    "для сегмента",
    "быстрая оценка информационного сигнала",
    "не дает однозначного рыночного сигнала",
    "скорее поддерживает рыночные ожидания",
)

_GENERIC_RISK_MARKERS = (
    "rss/быстрый анализ",
    "рыночная реакция зависит от ожиданий",
    "сигнал может измениться",
    "для отдельных акций важны ликвидность",
    "макроэффект зависит от будущих решений",
)


@dataclass
class NewsRow:
    id: int
    title: str
    slug: str
    source: str
    url: str
    payload_json: str
    asof: Optional[date]
    market: Optional[str]
    category: Optional[str]
    is_public: bool


class NewsRepositorySQL:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def list_public(self, limit: int = 50) -> List[News]:
        with self._session_factory() as session:
            return (
                session.query(News)
                .filter(News.is_public.is_(True))
                .order_by(News.asof.desc().nullslast(), News.updated_at.desc(), News.id.desc())
                .limit(limit)
                .all()
            )

    def get_public_by_id(self, news_id: int) -> Optional[News]:
        with self._session_factory() as session:
            return (
                session.query(News)
                .filter(News.id == news_id)
                .filter(News.is_public.is_(True))
                .one_or_none()
            )

    def to_news_block_out(self, b: News) -> NewsBlockOut:
        payload = self._safe_json_loads(b.payload_json)
        summary = str(payload.get("summary") or "").strip()
        bullets = payload.get("facts") or payload.get("bullets") or []
        bullets = [str(x).strip() for x in bullets if str(x).strip()]
        conclusion = payload.get("conclusion")
        conclusion = conclusion.strip() if isinstance(conclusion, str) else None
        market_meaning = payload.get("market_meaning")
        market_meaning = market_meaning.strip() if isinstance(market_meaning, str) else conclusion
        affected_segments = payload.get("affected_segments") or []
        affected_segments = [str(x).strip() for x in affected_segments if str(x).strip()]
        risks = payload.get("risks") or []
        risks = [str(x).strip() for x in risks if str(x).strip()]
        enhanced = self._enhance_public_analysis(
            title=b.title,
            summary=summary,
            facts=bullets,
            market_meaning=market_meaning,
            risks=risks,
            category=b.category,
        )
        market_meaning = enhanced["market_meaning"]
        conclusion = enhanced["market_meaning"]
        affected_segments = affected_segments or enhanced["affected_segments"]
        risks = enhanced["risks"]

        indicator_raw = payload.get("indicator") or {}
        indicator = None
        if isinstance(indicator_raw, dict):
            impact = indicator_raw.get("impact")
            confidence = indicator_raw.get("confidence")
            importance = indicator_raw.get("importance")
            rationale = indicator_raw.get("rationale") or []
            if impact in {"positive", "neutral", "negative"} and confidence in {"low", "medium", "high"}:
                indicator = NewsIndicatorOut(
                    impact=impact,
                    confidence=confidence,
                    importance=importance if importance in {"low", "medium", "high"} else None,
                    rationale=[str(x) for x in rationale if str(x).strip()],
                )

        if not summary:
            summary = "Краткое описание недоступно."

        return NewsBlockOut(
            id=b.id,
            slug=b.slug or slugify(b.title),
            title=b.title,
            source=b.source,
            url=b.url,
            summary=summary,
            bullets=bullets,
            conclusion=conclusion,
            market_meaning=market_meaning,
            affected_segments=affected_segments,
            risks=risks,
            indicator=indicator,
            asof=b.asof,
        )

    def upsert_by_url(
        self,
        *,
        url: str,
        title: str,
        slug: str,
        source: str,
        payload_json: str,
        asof: Optional[date] = None,
        market: Optional[str] = None,
        category: Optional[str] = None,
        is_public: bool = True,
    ) -> NewsRow:
        with self._session_factory() as session:
            row = session.query(News).filter(News.url == url).first()

            if row:
                row.title = title
                row.slug = slug
                row.source = source
                row.payload_json = payload_json
                row.asof = asof
                row.market = market
                row.category = category
                row.is_public = is_public
            else:
                row = News(
                    url=url,
                    title=title,
                    slug=slug,
                    source=source,
                    payload_json=payload_json,
                    asof=asof,
                    market=market,
                    category=category,
                    is_public=is_public,
                )
                session.add(row)

            session.commit()
            session.refresh(row)

        return NewsRow(
            id=row.id,
            title=row.title,
            slug=row.slug,
            source=row.source,
            url=row.url,
            payload_json=row.payload_json,
            asof=row.asof,
            market=row.market,
            category=row.category,
            is_public=row.is_public,
        )

    def get_public_by_slug(self, slug: str) -> Optional[News]:
        with self._session_factory() as session:
            return (
                session.query(News)
                .filter(News.slug == slug)
                .filter(News.is_public.is_(True))
                .order_by(News.id.desc())
                .first()
            )

    @staticmethod
    def _safe_json_loads(s: str) -> dict:
        try:
            payload = json.loads(s or "{}")
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _enhance_public_analysis(
        *,
        title: str,
        summary: str,
        facts: list[str],
        market_meaning: str | None,
        risks: list[str],
        category: str | None,
    ) -> dict:
        blob = " ".join([title or "", summary or "", *facts]).lower()
        current = (market_meaning or "").lower()
        is_generic = not market_meaning or any(marker in current for marker in _GENERIC_ANALYSIS_MARKERS)
        clean_risks = [
            risk
            for risk in risks
            if not any(marker in risk.lower() for marker in _GENERIC_RISK_MARKERS)
        ]

        if not is_generic and clean_risks:
            return {
                "market_meaning": market_meaning,
                "affected_segments": [],
                "risks": clean_risks,
            }

        def has(*words: str) -> bool:
            return any(word in blob for word in words)

        if has("дивиденд", "выплат"):
            return {
                "market_meaning": (
                    "Дивидендная рекомендация влияет на ожидаемую доходность акций и может поддержать интерес "
                    "к бумаге до закрытия реестра. Для рынка важны размер выплаты, дивидендная доходность и то, "
                    "насколько решение совпало с ожиданиями инвесторов."
                ),
                "affected_segments": ["дивидендные акции", "частные инвесторы", "финансовый сектор"],
                "risks": clean_risks
                or [
                    "Финальное решение остается за собранием акционеров.",
                    "Реакция акции зависит от того, была ли выплата уже заложена в цену.",
                    "После отсечки возможен дивидендный гэп.",
                ],
            }

        if has("зарплат", "доход") or has("розничн", "оборот"):
            return {
                "market_meaning": (
                    "Рост зарплат или розничного оборота указывает на устойчивый потребительский спрос. Это может "
                    "поддерживать выручку потребительских компаний, но одновременно сохранять инфляционное давление "
                    "и ограничивать пространство для смягчения денежно-кредитной политики."
                ),
                "affected_segments": ["потребительский сектор", "инфляция", "ставки"],
                "risks": clean_risks
                or [
                    "Сильный спрос может замедлить снижение инфляции.",
                    "Если Банк России увидит проинфляционный эффект, ожидания по снижению ставки могут ухудшиться.",
                    "Номинальный рост показателей важно сопоставлять с инфляцией и реальными доходами.",
                ],
            }

        if has("мфо", "займ"):
            return {
                "market_meaning": (
                    "Рост займов бизнесу через МФО показывает спрос на альтернативное финансирование, особенно "
                    "у малого и среднего бизнеса. Для рынка это сигнал о кредитной активности вне банковского "
                    "канала, но также о потенциально более высокой стоимости и рисках заемного капитала."
                ),
                "affected_segments": ["МСП", "кредитование", "финансовый сектор"],
                "risks": clean_risks
                or [
                    "Высокая стоимость микрофинансирования может повышать долговую нагрузку заемщиков.",
                    "Качество портфелей МФО зависит от деловой активности и ставок.",
                    "Данные по объему выдач не раскрывают качество заемщиков и просрочку.",
                ],
            }

        currency_signal = has("укреп", "ослаб", "валют", "курс") and has("рубл", "доллар", "евро")
        if currency_signal or has("нефт"):
            return {
                "market_meaning": (
                    "Укрепление рубля меняет баланс для экспортеров и импортеров: экспортная выручка в рублях "
                    "может снижаться, а импортные издержки — смягчаться. Связка с нефтью важна для бюджета, "
                    "валютной ликвидности и ожиданий по сырьевым компаниям."
                ),
                "affected_segments": ["рубль", "экспортеры", "нефть", "импортеры"],
                "risks": clean_risks
                or [
                    "Движение рубля может быстро измениться из-за нефти, валютных потоков и бюджетного правила.",
                    "Для экспортеров сильный рубль способен давить на рублевую выручку.",
                    "Эффект зависит от горизонта и устойчивости валютного движения.",
                ],
            }

        if has("индекс мос", "индекс москов"):
            return {
                "market_meaning": (
                    "Снижение индекса ниже психологического уровня отражает ухудшение настроений по широкому рынку. "
                    "Для инвесторов важны причины движения: ставки, нефть, дивидендные ожидания, санкционный фон "
                    "или продажи в отдельных тяжелых бумагах индекса."
                ),
                "affected_segments": ["индекс МосБиржи", "широкий рынок", "ликвидные акции"],
                "risks": clean_risks
                or [
                    "Пробой уровня может оказаться краткосрочным без подтверждения объемами торгов.",
                    "Индексное движение не всегда одинаково отражает ситуацию в отдельных секторах.",
                    "Дальнейшая динамика зависит от ставок, нефти, валюты и корпоративных новостей.",
                ],
            }

        if has("ipo", "ключев"):
            return {
                "market_meaning": (
                    "Связка IPO и ключевой ставки важна для первичного рынка: высокая доходность безрисковых "
                    "инструментов повышает требования инвесторов к новым размещениям. Поэтому активность IPO "
                    "зависит не только от уровня ставки, но и от качества эмитентов, оценки бизнеса и аппетита к риску."
                ),
                "affected_segments": ["IPO", "ставки", "рынок акций"],
                "risks": clean_risks
                or [
                    "Низкая ставка сама по себе не гарантирует спрос на размещения.",
                    "Слабое качество эмитентов или завышенная оценка могут ограничить интерес инвесторов.",
                    "Окно IPO зависит от общей ликвидности и настроений на рынке акций.",
                ],
            }

        if has("неликвидн", "иностранн", "акци"):
            return {
                "market_meaning": (
                    "Отказ от торгов неликвидными иностранными акциями снижает операционный и ликвидностный шум "
                    "на площадке. Для инвесторов это ограничивает доступ к части инструментов, но может повысить "
                    "качество торговой инфраструктуры и прозрачность ликвидности."
                ),
                "affected_segments": ["иностранные акции", "ликвидность", "Мосбиржа"],
                "risks": clean_risks
                or [
                    "Инвесторы с позициями в таких инструментах могут столкнуться с ограничениями выхода.",
                    "Снижение перечня инструментов уменьшает возможности диверсификации.",
                    "Важно отслеживать правила закрытия или переноса существующих позиций.",
                ],
            }

        default_segment = "макроэкономика" if category == "macro" else "рынок акций"
        return {
            "market_meaning": market_meaning
            or (
                "Новость важна как информационный сигнал для оценки текущих ожиданий по рынку. Ее эффект нужно "
                "сопоставлять с динамикой ставок, ликвидности, корпоративных событий и общим риск-аппетитом."
            ),
            "affected_segments": [default_segment],
            "risks": clean_risks
            or [
                "Влияние новости зависит от того, насколько событие уже учтено в ценах.",
                "Для точной оценки нужны дополнительные данные из первоисточника и реакция рынка.",
            ],
        }
