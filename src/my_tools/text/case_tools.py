import re


def split_words(text: str) -> list[str]:
    text = re.sub(r"[._\-\s]+", " ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    words = [w.lower() for w in text.split() if w]
    return words


def to_pascal_case(text: str) -> str:
    return "".join(w.capitalize() for w in split_words(text))


def to_camel_case(text: str) -> str:
    words = split_words(text)
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def to_snake_case(text: str) -> str:
    return "_".join(w.lower() for w in split_words(text))


def to_kebab_case(text: str) -> str:
    return "-".join(w.lower() for w in split_words(text))


def convert_case(text: str, style: str) -> str:
    if style == "pascal":
        return to_pascal_case(text)
    elif style == "camel":
        return to_camel_case(text)
    elif style == "snake":
        return to_snake_case(text)
    elif style == "kebab":
        return to_kebab_case(text)
    elif style == "upper":
        return text.upper()
    elif style == "lower":
        return text.lower()
    else:
        raise ValueError(f"不支持的命名风格: {style}")
