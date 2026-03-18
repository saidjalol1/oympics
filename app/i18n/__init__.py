"""Internationalization and translation support."""

from app.i18n.language import detect_language
from app.i18n.translations import TranslationManager, translations

__all__ = [
    "detect_language",
    "TranslationManager",
    "translations",
]
