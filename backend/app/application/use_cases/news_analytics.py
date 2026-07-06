from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.core.constants import CATEGORY_MACRO, CATEGORY_STOCKS

Impact = Literal["positive", "neutral", "negative"]
Confidence = Literal["low", "medium", "high"]

_WS_RE = re.compile(r"\s+")
_CYRILLIC_RE = re.compile(r"[а-яА-ЯёЁ]")
_LATIN_RE = re.compile(r"[a-zA-Z]")
_DATE_HEADLINE_RE = re.compile(
    r"(?:^|\s)(\d{2}\.\d{2}\.\d{2,4})\s+(.+?)(?=\s+\d{2}\.\d{2}\.\d{2,4}\s+|$)"
)
_SENTENCE_RE = re.compile(r"[^.!?。！？]+[.!?]?", re.U)
_LEADING_DATETIME_RE = re.compile(
    r"^(?:(?:\d{1,2}:\d{2})(?:\s+\d{2}\.\d{2}\.\d{2,4})?|(?:\d{2}\.\d{2}\.\d{2,4}))[\s,;:–—-]+"
)
_DATE_ANYWHERE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{2,4}\b")
_TIME_ANYWHERE_RE = re.compile(r"\b\d{1,2}:\d{2}\b")

_NAVIGATION_WORDS = {
    "пресс-центр",
    "министерство",
    "документы",
    "обращения",
    "контакты",
    "открытое министерство",
    "государственные услуги",
    "официальная позиция",
    "информационные системы",
    "финансовая грамотность",
    "covid",
    "материалов",
}

_TECHNICAL_NOISE_WORDS = {
    "тестового полигона",
    "tks spectra",
    "ткс spectra",
    "spectra",
    "срочного рынка",
    "репо",
    "офз выпуск",
    "аукционов по размещению",
    "нижней границы ценового коридора",
    "ценового коридора",
    "диапазона оценки процентных рисков",
    "процентных рисков",
    "техническ",
}

_POSITIVE_PATTERNS = {
    "снизил": "снижение ставки/нагрузки может поддержать оценку активов",
    "снизила": "снижение ставки/нагрузки может поддержать оценку активов",
    "снижение": "снижение ставки/нагрузки может поддержать оценку активов",
    "рост": "рост показателей обычно улучшает ожидания рынка",
    "вырос": "рост показателей обычно улучшает ожидания рынка",
    "выросла": "рост показателей обычно улучшает ожидания рынка",
    "рост прибыли": "рост прибыли поддерживает инвестиционный интерес",
    "увеличил прибыль": "рост прибыли поддерживает инвестиционный интерес",
    "увеличила прибыль": "рост прибыли поддерживает инвестиционный интерес",
    "вернул": "возврат к прибыли поддерживает инвестиционный интерес",
    "дивиденд": "дивидендные новости могут повысить интерес инвесторов",
    "рекорд": "рекордные показатели усиливают позитивную оценку",
}

_NEGATIVE_PATTERNS = {
    "повысил": "рост ставки/нагрузки может давить на оценки активов",
    "повысила": "рост ставки/нагрузки может давить на оценки активов",
    "повышение": "рост ставки/нагрузки может давить на оценки активов",
    "инфляц": "инфляционные риски могут удерживать жесткие финансовые условия",
    "санкц": "санкционные ограничения повышают неопределенность",
    "падение": "снижение показателей может ухудшать ожидания рынка",
    "упал": "падение цены, индекса или показателя ухудшает рыночный сигнал",
    "упала": "падение цены, индекса или показателя ухудшает рыночный сигнал",
    "упали": "падение цены, индекса или показателя ухудшает рыночный сигнал",
    "ниже": "пробой или уход ниже важного уровня усиливает осторожность рынка",
    "подешев": "снижение цены актива или сырья может давить на ожидания",
    "сократ": "сокращение финансового результата или активности ухудшает сигнал",
    "замедл": "замедление показателей ухудшает ожидания рынка",
    "снизилась": "снижение показателей может ухудшать ожидания рынка",
    "убыт": "убытки ухудшают восприятие финансовой устойчивости",
    "дефолт": "дефолты повышают кредитные риски и осторожность инвесторов",
    "задержал выплат": "задержка выплат повышает кредитные и корпоративные риски",
    "задержк": "задержка выплат или обязательств повышает риски",
    "нелегальн": "рост нелегальной активности на финрынке повышает регуляторные риски",
    "дефицит": "дефицит может усиливать бюджетные или корпоративные риски",
    "риск": "явное упоминание рисков повышает осторожность оценки",
}

_HIGH_SIGNAL_PATTERNS = {
    "ключев": "ключевая ставка напрямую влияет на доходности и стоимость капитала",
    "ставк": "ставки напрямую влияют на доходности и стоимость капитала",
    "инфляц": "инфляция важна для денежно-кредитной политики",
    "дивиденд": "дивиденды напрямую влияют на ожидания по акциям",
    "индекс": "индексные новости важны для широкого рынка",
    "торг": "торговая инфраструктура влияет на доступность и ликвидность рынка",
    "листинг": "листинг влияет на доступность инструмента для инвесторов",
}


@dataclass(frozen=True)
class NewsAnalysis:
    summary: str
    facts: list[str]
    conclusion: str
    risks: list[str]
    impact: Impact
    confidence: Confidence
    rationale: list[str]

    def to_payload(self) -> dict:
        return {
            "summary": self.summary,
            "facts": self.facts,
            "conclusion": self.conclusion,
            "risks": self.risks,
            "indicator": {
                "impact": self.impact,
                "confidence": self.confidence,
                "rationale": self.rationale,
            },
            "_source_type": "rules",
        }


def build_fast_news_analysis(
    *,
    title: str,
    text: str,
    source: str,
    category: str,
    personalized_hint: str | None = None,
) -> NewsAnalysis:
    title = _clean(title, 240)
    text = _clean(text, 4000)
    fragments = _extract_news_fragments(text)
    best_fragment = _best_fragment(fragments, title)
    useful_text = " ".join([best_fragment or title, *fragments[:2]])
    blob = f"{title} {useful_text}".lower()

    positive_reasons = _matches(blob, _POSITIVE_PATTERNS)
    negative_reasons = _matches(blob, _NEGATIVE_PATTERNS)
    signal_reasons = _matches(blob, _HIGH_SIGNAL_PATTERNS)

    if len(positive_reasons) > len(negative_reasons):
        impact: Impact = "positive"
        direction = "скорее поддерживает рыночные ожидания"
    elif len(negative_reasons) > len(positive_reasons):
        impact = "negative"
        direction = "может усиливать осторожность инвесторов"
    else:
        impact = "neutral"
        direction = "не дает однозначного рыночного сигнала"

    confidence: Confidence = "medium" if signal_reasons else "low"
    if len(positive_reasons) + len(negative_reasons) >= 2 and signal_reasons:
        confidence = "high"

    category_label = "макроэкономика РФ" if category == CATEGORY_MACRO else "российский рынок акций"
    summary = _human_summary(title=title, source=source, category=category, fragments=fragments)

    conclusion = (
        f"Для сегмента '{category_label}' новость {direction}. "
        "Это не инвестиционная рекомендация, а быстрая оценка информационного сигнала."
    )
    if personalized_hint:
        conclusion = f"{conclusion} {personalized_hint}"

    facts = _content_facts(title=title, summary=summary, fragments=fragments)
    if signal_reasons:
        facts.append(signal_reasons[0])

    risks = _risks_for(category=category, impact=impact)
    rationale = (positive_reasons if impact == "positive" else negative_reasons if impact == "negative" else [])
    rationale = rationale[:2] + signal_reasons[:2]
    if not rationale:
        rationale = ["В тексте нет сильных ключевых сигналов для уверенной оценки."]

    return NewsAnalysis(
        summary=summary,
        facts=_dedupe(facts)[:5],
        conclusion=conclusion,
        risks=risks,
        impact=impact,
        confidence=confidence,
        rationale=_dedupe(rationale)[:4],
    )


def looks_like_technical_news(title: str, text: str, source: str = "") -> bool:
    blob = f"{source} {title} {text}"
    return _technical_noise_score(blob) >= 2


def looks_russian(text: str) -> bool:
    text = text or ""
    cyrillic = len(_CYRILLIC_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    if cyrillic == 0:
        return False
    return cyrillic >= latin * 0.35


def _matches(text: str, patterns: dict[str, str]) -> list[str]:
    return [reason for pattern, reason in patterns.items() if pattern in text]


def _risks_for(*, category: str, impact: Impact) -> list[str]:
    risks = [
        "RSS/быстрый анализ может не учитывать полный текст первоисточника.",
        "Рыночная реакция зависит от ожиданий инвесторов и общего новостного фона.",
    ]
    if category == CATEGORY_STOCKS:
        risks.append("Для отдельных акций важны ликвидность, отчетность и корпоративные события.")
    else:
        risks.append("Макроэффект зависит от будущих решений регуляторов и динамики инфляции.")
    if impact != "neutral":
        risks.append("Сигнал может измениться после публикации дополнительных деталей.")
    return risks


def _clean(value: str, max_chars: int) -> str:
    text = _WS_RE.sub(" ", (value or "").strip())
    if len(text) <= max_chars:
        return text
    clipped = _clip_at_boundary(text, max_chars)
    return clipped or text[:max_chars].rstrip()


def _extract_news_fragments(text: str) -> list[str]:
    text = _WS_RE.sub(" ", (text or "").strip())
    fragments: list[str] = []

    for _, headline in _DATE_HEADLINE_RE.findall(text):
        headline = _cleanup_fragment(headline)
        if _is_good_fragment(headline):
            fragments.append(headline)
        if len(fragments) >= 5:
            break

    if fragments:
        return _dedupe(fragments)

    sentences = []
    candidates: list[str] = []
    for part in re.split(r"\s*;\s*", text):
        candidates.extend(match.group(0) for match in _SENTENCE_RE.finditer(part))

    for candidate in candidates:
        sentence = _cleanup_fragment(candidate)
        if _is_good_fragment(sentence):
            sentences.append(sentence)
        if len(sentences) >= 4:
            break
    return _dedupe(sentences)


def _readable_excerpt(text: str, max_chars: int) -> str:
    fragments = _extract_news_fragments(text)
    if fragments:
        return " ".join(fragments[:2])

    text = _cleanup_fragment(text)
    clipped = _clip_at_boundary(text, max_chars)
    return clipped or text[:max_chars].rstrip()


def _cleanup_fragment(value: str) -> str:
    text = _WS_RE.sub(" ", (value or "").strip(" \t\r\n-–—:;,."))
    text = _strip_leading_datetime(text)
    text = _DATE_ANYWHERE_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip(" \t\r\n-–—:;,.")
    text = re.sub(r"^\d+\s+материал(?:ов|а)?\s+", "", text, flags=re.I)
    return _clip_at_boundary(text, 240) or text[:240].rstrip()


def _strip_leading_datetime(text: str) -> str:
    prev = ""
    out = text
    while prev != out:
        prev = out
        out = _LEADING_DATETIME_RE.sub("", out).strip()
    return out


def _digit_ratio(text: str) -> float:
    meaningful = [ch for ch in text if ch.isalnum()]
    if not meaningful:
        return 0.0
    return sum(ch.isdigit() for ch in meaningful) / len(meaningful)


def _technical_noise_score(text: str) -> int:
    lower = text.lower()
    score = sum(marker in lower for marker in _TECHNICAL_NOISE_WORDS)
    if _digit_ratio(text) > 0.18:
        score += 1
    if len(_TIME_ANYWHERE_RE.findall(text)) >= 2:
        score += 1
    return score


def _best_fragment(fragments: list[str], title: str) -> str | None:
    good = [f for f in fragments if _is_good_fragment(f)]
    if not good:
        return None
    return good[0]


def _human_summary(*, title: str, source: str, category: str, fragments: list[str]) -> str:
    best = _best_fragment(fragments, title)
    clean_title = _cleanup_fragment(title)
    source_lower = source.lower()

    if best and _technical_noise_score(best) < 2:
        return _ensure_sentence(best)

    if "moex" in source_lower or "московская биржа" in source_lower:
        return "МосБиржа опубликовала сообщение по торговой инфраструктуре."

    if clean_title and _is_good_fragment(clean_title):
        return _ensure_sentence(clean_title)

    if category == CATEGORY_MACRO:
        return "Опубликована макроэкономическая новость, важная для оценки рынка РФ."
    return "Опубликована новость по российскому рынку акций и торговой инфраструктуре."


def _content_facts(*, title: str, summary: str, fragments: list[str]) -> list[str]:
    out: list[str] = []
    for fragment in fragments:
        fact = _ensure_sentence(fragment)
        if len(fact) > 180:
            continue
        if _is_near_duplicate(fact, title) or _is_near_duplicate(fact, summary):
            continue
        out.append(fact)
        if len(out) >= 3:
            break
    return out


def _is_near_duplicate(left: str, right: str) -> bool:
    a = set(re.findall(r"[а-яА-ЯёЁa-zA-Z0-9]{4,}", left.lower()))
    b = set(re.findall(r"[а-яА-ЯёЁa-zA-Z0-9]{4,}", right.lower()))
    if not a or not b:
        return False
    return len(a & b) / max(1, min(len(a), len(b))) >= 0.75


def _ensure_sentence(text: str) -> str:
    text = _WS_RE.sub(" ", (text or "").strip(" \t\r\n-–—:;,."))
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _is_good_fragment(value: str) -> bool:
    text = (value or "").strip()
    lower = text.lower()
    if len(text) < 24 or len(text) > 260:
        return False
    if not looks_russian(text):
        return False
    navigation_hits = sum(word in lower for word in _NAVIGATION_WORDS)
    if navigation_hits >= 2:
        return False
    if lower.count(" ") < 3:
        return False
    if _digit_ratio(text) > 0.28:
        return False
    if _technical_noise_score(text) >= 2:
        return False
    return True


def _clip_at_boundary(text: str, max_chars: int) -> str:
    text = _WS_RE.sub(" ", (text or "").strip())
    if len(text) <= max_chars:
        return text

    window = text[:max_chars].rstrip()
    for sep in (". ", "! ", "? ", "; "):
        pos = window.rfind(sep)
        if pos >= max(40, max_chars // 2):
            return window[: pos + 1].rstrip()

    comma = window.rfind(", ")
    if comma >= max(40, max_chars // 2):
        return window[:comma].rstrip()
    space = window.rfind(" ")
    if space >= max(40, max_chars // 2):
        return window[:space].rstrip()
    return window.rstrip()


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out
