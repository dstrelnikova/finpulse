import re


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-я0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
