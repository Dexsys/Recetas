import re

import bleach
from bleach.css_sanitizer import CSSSanitizer
from markupsafe import escape


_HTML_TAG_PATTERN = re.compile(r"</?[a-zA-Z][^>]*>")
_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "mark",
    "ul",
    "ol",
    "li",
    "blockquote",
    "span",
]
_ALLOWED_ATTRS = {
    "span": ["style"],
}
_CSS_SANITIZER = CSSSanitizer(allowed_css_properties=["background-color"])


def sanitize_rich_text(value):
    if not value:
        return ""

    cleaned = bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
        css_sanitizer=_CSS_SANITIZER,
    )
    return cleaned.strip()


def normalize_rich_text_for_editor(value):
    if not value:
        return ""

    # Compatibilidad con contenido historico guardado como texto plano.
    if _HTML_TAG_PATTERN.search(value):
        return sanitize_rich_text(value)

    return str(escape(value)).replace("\n", "<br>")
