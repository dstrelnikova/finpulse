from app.application.use_cases.news_analytics import build_fast_news_analysis, looks_russian
from app.core.constants import CATEGORY_MACRO, CATEGORY_STOCKS


def test_fast_news_analysis_detects_negative_macro_signal():
    analysis = build_fast_news_analysis(
        title="Банк России повысил ключевую ставку",
        text="Регулятор отметил инфляционные риски и жесткие денежно-кредитные условия.",
        source="Банк России",
        category=CATEGORY_MACRO,
    )

    assert analysis.impact == "negative"
    assert analysis.confidence in {"medium", "high"}
    assert analysis.conclusion
    assert analysis.risks


def test_fast_news_analysis_detects_positive_stock_signal():
    analysis = build_fast_news_analysis(
        title="Компания объявила дивиденды и рост прибыли",
        text="Совет директоров рекомендовал дивиденды после роста прибыли.",
        source="MOEX",
        category=CATEGORY_STOCKS,
    )

    assert analysis.impact == "positive"
    assert any("дивиденд" in reason.lower() for reason in analysis.rationale)


def test_fast_news_analysis_detects_index_drop_as_negative():
    analysis = build_fast_news_analysis(
        title="Индекс Мосбиржи упал ниже 2600 пунктов впервые с ноября 2025 года",
        text="Индекс Мосбиржи упал ниже важного уровня на фоне давления продавцов.",
        source="Коммерсантъ Финансы",
        category=CATEGORY_STOCKS,
    )

    assert analysis.impact == "negative"
    assert analysis.confidence in {"medium", "high"}


def test_fast_news_analysis_detects_profit_decline_as_negative():
    analysis = build_fast_news_analysis(
        title='Российские "дочки" RBI в I квартале сократили прибыль на 39%',
        text="Прибыль дочерних структур сократилась на 39% относительно прошлого периода.",
        source="Интерфакс Бизнес",
        category=CATEGORY_STOCKS,
    )

    assert analysis.impact == "negative"


def test_looks_russian_rejects_english_market_news():
    assert not looks_russian("Risk parameters change for the security SU26231RMFS9")
    assert looks_russian("Московская биржа изменила параметры риска по облигации")


def test_fast_news_analysis_removes_source_navigation_text():
    raw_text = (
        "Минфин России :: Пресс-центр Министерство Деятельность Документы Обращения "
        "Исполнение судебных актов Контакты Работа в Минфине Пресс-центр Организационная "
        "структура Государственная служба Открытое министерство Планирование деятельности "
        "Государственные услуги и функции Открытые данные Статистика Информационные системы "
        "Финансовая грамотность Противодействие коррупции COVID-19 80 лет Победе "
        "Пресс-центр контакты для СМИ Все Анонсы Интервью Новости Официальная позиция СМИ "
        "7838 материалов 27.04.26 Залог успешного IPO: рекомендации регуляторов "
        "24.04.26 Предложены новые правила регулирования трансграничной электронной торговли "
        "24.04.26 Иван Чебесков: Токенизация реальных активов способна стать следующим этапом "
        "масштабирования российского финансового рынка"
    )

    analysis = build_fast_news_analysis(
        title="Рынок РФ — макрообзор",
        text=raw_text,
        source="minfin.gov.ru",
        category=CATEGORY_MACRO,
    )

    assert "Пресс-центр Министерство Деятельность" not in analysis.summary
    assert "Залог успешного IPO" in analysis.summary
    assert any("Предложены новые правила" in fact for fact in analysis.facts)
    assert not analysis.summary.endswith(("...", "…"))


def test_fast_news_analysis_cleans_moex_datetime_noise():
    raw_text = (
        "16:29 Обновление тестового полигона Срочного рынка T1 до версии TКС Spectra 9.6; "
        "16:06 28.04.2026 изменены значения нижней границы ценового коридора РЕПО, "
        "ставки переноса и диапазона оценки процентных рисков ценной бумаги LEAS; "
        "16:01 О проведении 29 апреля 2026 года аукционов по размещению ОФЗ выпусков № 26218RMFS"
    )

    analysis = build_fast_news_analysis(
        title="Рынок РФ — обзор акций",
        text=raw_text,
        source="www.moex.com",
        category=CATEGORY_STOCKS,
    )

    assert analysis.summary == "МосБиржа опубликовала сообщение по торговой инфраструктуре."
    assert not analysis.summary[:5].strip().replace(":", "").isdigit()
    assert len(analysis.summary) <= 240


def test_fast_news_analysis_keeps_readable_macro_summary():
    analysis = build_fast_news_analysis(
        title="Инфляционные ожидания населения в апреле снизились",
        text=(
            "Инфляционные ожидания населения в апреле снизились, "
            "но пока остаются в диапазоне 4–5% в пересчете на год."
        ),
        source="Банк России",
        category=CATEGORY_MACRO,
    )

    assert "Инфляционные ожидания" in analysis.summary
    assert not analysis.summary.startswith("Новость:")
    assert not any(fact.startswith(("Источник:", "Тема:")) for fact in analysis.facts)
