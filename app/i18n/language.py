"""
Language detection from HTTP Accept-Language header.

This module provides functionality to detect user language preference from
the Accept-Language HTTP header and return one of the supported language codes.

Supported languages:
- en: English
- ru: Russian (Русский)
- uz: Uzbek (O'zbek)
"""

from typing import Optional


def detect_language(accept_language: Optional[str]) -> str:
    """
    Parse Accept-Language header and return supported language code.
    
    This function analyzes the Accept-Language header to determine the user's
    preferred language. It supports English (en), Russian (ru), and Uzbek (uz).
    If the header is missing or contains only unsupported languages, it defaults
    to English.
    
    The function handles various Accept-Language header formats:
    - Simple language codes: "en", "ru", "uz"
    - Language with region: "en-US", "ru-RU", "uz-UZ"
    - Multiple languages with quality values: "en-US,en;q=0.9,ru;q=0.8"
    - Complex headers with multiple preferences
    
    Args:
        accept_language: The Accept-Language header value from the HTTP request.
                        Can be None if the header is not present.
    
    Returns:
        A supported language code: "en", "ru", or "uz". Defaults to "en" if
        the header is missing or contains no supported languages.
    
    Examples:
        >>> detect_language("en-US,en;q=0.9")
        'en'
        >>> detect_language("ru-RU,ru;q=0.9")
        'ru'
        >>> detect_language("uz-UZ,uz;q=0.9")
        'uz'
        >>> detect_language("fr-FR,fr;q=0.9")
        'en'
        >>> detect_language(None)
        'en'
        >>> detect_language("")
        'en'
    
    Requirements:
        - 7.1: Detect language from Accept-Language header
        - 7.2: Return "en" for English
        - 7.3: Return "ru" for Russian
        - 7.4: Return "uz" for Uzbek
        - 7.5: Default to "en" when header is missing or unsupported
    """
    # Default to English if header is missing or empty
    if not accept_language:
        return "en"
    
    # Supported language codes
    supported_languages = {"en", "ru", "uz"}
    
    # Parse the Accept-Language header
    # Format: "en-US,en;q=0.9,ru;q=0.8" or "en" or "en-US"
    # Split by comma to get individual language preferences
    language_preferences = accept_language.lower().split(",")
    
    for preference in language_preferences:
        # Remove quality value (e.g., ";q=0.9") if present
        language_code = preference.split(";")[0].strip()
        
        # Extract the primary language code (before the hyphen)
        # e.g., "en-US" -> "en", "ru-RU" -> "ru"
        primary_code = language_code.split("-")[0].strip()
        
        # Check if the primary code is supported
        if primary_code in supported_languages:
            return primary_code
    
    # Default to English if no supported language found
    return "en"
