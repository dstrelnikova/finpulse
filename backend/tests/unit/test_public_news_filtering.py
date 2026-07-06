from app.application.use_cases.public_news.public_news import GetPublicNewsFeed
from app.presentation.schemas.summary import NewsBlockOut, NewsIndicatorOut


def test_public_feed_hides_generic_moex_technical_fallback():
    item = NewsBlockOut(
        id=1,
        slug="market-brief",
        title="Рынок РФ — обзор акций",
        source="www.moex.com",
        url="https://www.moex.com/ru/news/",
        summary=(
            "В источнике опубликованы материалы: 16:29 Обновление тестового полигона Срочного рынка "
            "Т1 до версии ТКС Spectra 9.6; изменены значения нижней границы ценового коридора РЕПО."
        ),
        bullets=[],
        conclusion=None,
        risks=[],
        indicator=NewsIndicatorOut(
            impact="negative",
            confidence="medium",
            rationale=["явное упоминание рисков повышает осторожность оценки"],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is False


def test_public_feed_skips_low_value_calendar_news():
    item = NewsBlockOut(
        id=2,
        slug="cbr-payment-system",
        title="Информация о работе платежной системы Банка России 11 мая 2026 года",
        source="Банк России",
        url="https://www.cbr.ru/press/PR/?file=example.htm",
        summary="Банк России подтвердил функционирование платежной системы в обычном режиме 11 мая 2026 года.",
        bullets=[],
        conclusion=None,
        risks=[],
        indicator=NewsIndicatorOut(
            impact="neutral",
            confidence="low",
            rationale=["Сообщение носит информативный характер."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is False


def test_public_feed_skips_payment_system_schedule_even_with_facts():
    item = NewsBlockOut(
        id=6,
        slug="payment-system",
        title="Информация о работе платежной системы Банка России 11 мая 2026 года",
        source="Банк России",
        url="https://www.cbr.ru/press/PR/?file=payment.htm",
        summary="Банк России сообщил график работы платежной системы.",
        bullets=[
            "Платежная система Банка России продолжит работу согласно установленному графику.",
            "Регулярный сеанс пройдет с 08:00 до 21:00 московского времени.",
        ],
        conclusion="Новость носит календарный характер.",
        risks=["Рыночный эффект ограничен справочным характером сообщения."],
        indicator=NewsIndicatorOut(
            impact="neutral",
            confidence="medium",
            rationale=["Сообщение описывает расписание работы инфраструктуры."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is False


def test_public_feed_skips_low_confidence_even_with_some_facts():
    item = NewsBlockOut(
        id=5,
        slug="low-confidence",
        title="Банк России расширяет доступ к информации об участниках финансового рынка",
        source="Банк России",
        url="https://www.cbr.ru/press/event/?id=5",
        summary="Банк России сообщил о расширении доступа к сводной информации.",
        bullets=[
            "Банк России расширяет доступ к сводной информации об участниках финансового рынка.",
            "Изменение касается раскрытия данных для пользователей финансовой информации.",
        ],
        conclusion="Новость может быть полезна для прозрачности рынка.",
        risks=["Детали изменений в доступе к информации пока не раскрыты."],
        indicator=NewsIndicatorOut(
            impact="neutral",
            confidence="low",
            rationale=["Недостаточно конкретных данных для уверенной оценки."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is False


def test_public_feed_keeps_meaningful_low_confidence_negative_item():
    item = NewsBlockOut(
        id=7,
        slug="bond-defaults",
        title="Дефолты собирают облигационный портфель",
        source="Коммерсантъ Финансы",
        url="https://www.kommersant.ru/doc/example",
        summary="На рынке облигаций все больше рисков.",
        bullets=[
            "Под угрозой дефолта примерно четверть бумаг, сообщили аналитики финансового рынка.",
            "В первом квартале компании 11 раз переносили выплаты по кредитным договорам.",
            "Часть случаев переросла в полноценные дефолты перед инвесторами.",
        ],
        conclusion="Рост дефолтов усиливает кредитные риски на рынке облигаций.",
        risks=["Реакция зависит от качества эмитентов и структуры портфелей инвесторов."],
        indicator=NewsIndicatorOut(
            impact="negative",
            confidence="low",
            rationale=["Дефолты повышают кредитные риски и осторожность инвесторов."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is True


def test_public_feed_skips_payload_rejected_by_gigachat_quality():
    payload = {
        "summary": "МосБиржа сообщила о тестовом контуре.",
        "quality": {
            "is_public_feed_worthy": False,
            "is_technical_noise": True,
            "reason": "Техническое служебное сообщение.",
        },
    }

    assert GetPublicNewsFeed._is_payload_public_worthy(payload) is False


def test_public_feed_skips_low_information_item():
    item = NewsBlockOut(
        id=3,
        slug="low-info",
        title="Денежная масса в марте снизилась, рост кредита экономике замедлился",
        source="Банк России",
        url="https://www.cbr.ru/press/event/?id=1",
        summary="Денежная масса в марте снизилась, рост кредита экономике замедлился.",
        bullets=[],
        conclusion=None,
        risks=["В анонсе мало проверяемых фактов; подробности лучше сверить в источнике."],
        indicator=NewsIndicatorOut(
            impact="positive",
            confidence="low",
            rationale=["Снижение ставки/нагрузки может поддержать оценку активов."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is False


def test_public_feed_skips_rss_only_low_info_payload():
    payload = {
        "_content_quality": "rss_only",
        "summary": "Денежная масса в марте снизилась.",
        "facts": ["Конкретная величина снижения не указана."],
        "risks": ["Полный текст источника недоступен."],
        "indicator": {
            "impact": "neutral",
            "confidence": "low",
            "importance": "low",
            "rationale": [],
        },
        "quality": {
            "is_public_feed_worthy": True,
            "is_technical_noise": False,
        },
    }

    assert GetPublicNewsFeed._is_payload_public_worthy(payload) is False


def test_public_feed_keeps_meaningful_recent_item():
    item = NewsBlockOut(
        id=4,
        slug="inflation",
        title="Инфляционные ожидания населения в апреле снизились",
        source="Банк России",
        url="https://www.cbr.ru/press/event/?id=2",
        summary="Банк России сообщил о снижении инфляционных ожиданий населения в апреле.",
        bullets=[
            "Инфляционные ожидания населения снизились в апреле, следует из сообщения Банка России.",
            "Показатель важен для оценки будущей инфляции и решений по денежно-кредитной политике.",
        ],
        conclusion="Снижение инфляционных ожиданий может быть умеренно позитивным сигналом для рынка ставок.",
        risks=["Эффект зависит от дальнейшей динамики цен и решений регулятора."],
        indicator=NewsIndicatorOut(
            impact="positive",
            confidence="medium",
            rationale=["Инфляционные ожидания важны для денежно-кредитной политики."],
        ),
        asof=None,
    )

    assert GetPublicNewsFeed._is_public_item_eligible(item) is True
