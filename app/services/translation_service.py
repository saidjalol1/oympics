"""Translation service for multi-language content validation and conversion.

This module provides the TranslationService class for handling multi-language
content validation, translation retrieval with fallback logic, and conversion
between new multi-language format and legacy single-field format.
"""

from typing import Any, Optional
from app.core.exceptions import ValidationError


class TranslationService:
    """Service for multi-language content validation and conversion.
    
    Handles validation of multi-language fields, translation retrieval with
    fallback logic, and conversion between new multi-language format and
    legacy single-field format for backward compatibility.
    
    Constants:
        SUPPORTED_LANGUAGES: List of supported language codes (en, uz, ru)
        DEFAULT_LANGUAGE: Default language code (en)
    """
    
    SUPPORTED_LANGUAGES = ["en", "uz", "ru"]
    DEFAULT_LANGUAGE = "en"
    
    def validate_translations(
        self,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        text_en: Optional[str] = None,
        text_uz: Optional[str] = None,
        text_ru: Optional[str] = None,
        field_name: str = "field"
    ) -> None:
        """Validate that all required language fields are present and non-empty.
        
        Validates that translations are provided for all three supported languages
        (English, Uzbek, Russian) and that each translation is a non-empty string.
        
        Args:
            name_en: English name/title (optional, used for name fields)
            name_uz: Uzbek name/title (optional, used for name fields)
            name_ru: Russian name/title (optional, used for name fields)
            text_en: English text (optional, used for text fields)
            text_uz: Uzbek text (optional, used for text fields)
            text_ru: Russian text (optional, used for text fields)
            field_name: Name of the field being validated (for error messages)
            
        Raises:
            ValidationError: If any translation is missing or empty
            
        Examples:
            >>> service = TranslationService()
            >>> service.validate_translations(
            ...     name_en="Math", name_uz="Matematika", name_ru="Математика"
            ... )
            >>> # No exception raised - all translations valid
            
            >>> service.validate_translations(
            ...     name_en="Math", name_uz="", name_ru="Математика"
            ... )
            ValidationError: Uzbek translation for field is required
        """
        # Determine which set of fields to validate (name or text)
        if name_en is not None or name_uz is not None or name_ru is not None:
            translations = {
                "en": name_en,
                "uz": name_uz,
                "ru": name_ru
            }
        elif text_en is not None or text_uz is not None or text_ru is not None:
            translations = {
                "en": text_en,
                "uz": text_uz,
                "ru": text_ru
            }
        else:
            raise ValidationError(f"No translations provided for {field_name}")
        
        # Validate each language
        missing_languages = []
        empty_languages = []
        
        for lang_code in self.SUPPORTED_LANGUAGES:
            translation = translations.get(lang_code)
            
            if translation is None:
                missing_languages.append(lang_code)
            elif not isinstance(translation, str):
                raise ValidationError(
                    f"{self._get_language_name(lang_code)} translation for {field_name} "
                    f"must be a string"
                )
            elif not translation.strip():
                empty_languages.append(lang_code)
        
        # Report missing translations
        if missing_languages:
            lang_names = [self._get_language_name(code) for code in missing_languages]
            raise ValidationError(
                f"{', '.join(lang_names)} translation(s) for {field_name} required"
            )
        
        # Report empty translations
        if empty_languages:
            lang_names = [self._get_language_name(code) for code in empty_languages]
            raise ValidationError(
                f"{', '.join(lang_names)} translation(s) for {field_name} cannot be empty"
            )
    
    def get_translation(
        self,
        entity: Any,
        field_prefix: str,
        language: str
    ) -> str:
        """Get translation for a specific language with fallback logic.
        
        Retrieves the translation for the requested language. If the translation
        is not available, falls back to English. If English is not available,
        returns the first available translation.
        
        Fallback order:
        1. Requested language
        2. English (DEFAULT_LANGUAGE)
        3. First available language
        
        Args:
            entity: Entity object with translation fields (e.g., Subject, Level)
            field_prefix: Field prefix (e.g., "name" or "text")
            language: Requested language code (en, uz, ru)
            
        Returns:
            Translation string in the requested or fallback language
            
        Raises:
            ValidationError: If no translations are available
            
        Examples:
            >>> subject = Subject(name_en="Math", name_uz="Matematika", name_ru="Математика")
            >>> service = TranslationService()
            >>> service.get_translation(subject, "name", "uz")
            'Matematika'
            
            >>> service.get_translation(subject, "name", "fr")  # Unsupported language
            'Math'  # Falls back to English
        """
        # Validate language code
        if language not in self.SUPPORTED_LANGUAGES:
            language = self.DEFAULT_LANGUAGE
        
        # Try requested language
        field_name = f"{field_prefix}_{language}"
        translation = getattr(entity, field_name, None)
        
        if translation and isinstance(translation, str) and translation.strip():
            return translation
        
        # Fallback to English
        if language != self.DEFAULT_LANGUAGE:
            field_name = f"{field_prefix}_{self.DEFAULT_LANGUAGE}"
            translation = getattr(entity, field_name, None)
            
            if translation and isinstance(translation, str) and translation.strip():
                return translation
        
        # Fallback to first available language
        for lang_code in self.SUPPORTED_LANGUAGES:
            field_name = f"{field_prefix}_{lang_code}"
            translation = getattr(entity, field_name, None)
            
            if translation and isinstance(translation, str) and translation.strip():
                return translation
        
        # No translations available
        raise ValidationError(
            f"No translations available for {field_prefix} on entity {type(entity).__name__}"
        )
    
    def prepare_legacy_field(
        self,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        text_en: Optional[str] = None,
        text_uz: Optional[str] = None,
        text_ru: Optional[str] = None
    ) -> str:
        """Prepare legacy name/text field from translations.
        
        Creates a legacy single-field value from multi-language translations
        for backward compatibility. Uses English translation by default.
        
        Args:
            name_en: English name (optional, used for name fields)
            name_uz: Uzbek name (optional, used for name fields)
            name_ru: Russian name (optional, used for name fields)
            text_en: English text (optional, used for text fields)
            text_uz: Uzbek text (optional, used for text fields)
            text_ru: Russian text (optional, used for text fields)
            
        Returns:
            Legacy field value (English translation or first available)
            
        Examples:
            >>> service = TranslationService()
            >>> service.prepare_legacy_field(
            ...     name_en="Math", name_uz="Matematika", name_ru="Математика"
            ... )
            'Math'
        """
        # Determine which set of fields to use
        if name_en is not None or name_uz is not None or name_ru is not None:
            translations = [name_en, name_uz, name_ru]
            # Prefer English
            if name_en:
                return name_en
        elif text_en is not None or text_uz is not None or text_ru is not None:
            translations = [text_en, text_uz, text_ru]
            # Prefer English
            if text_en:
                return text_en
        else:
            return ""
        
        # Return first available translation
        for translation in translations:
            if translation and isinstance(translation, str) and translation.strip():
                return translation
        
        return ""
    
    def handle_legacy_input(
        self,
        legacy_value: str,
        field_type: str = "name"
    ) -> dict[str, str]:
        """Convert legacy single-field input to multi-language format.
        
        Converts a legacy single-field value (name or text) to the new
        multi-language format by copying the value to all three language fields.
        This ensures backward compatibility with existing API clients.
        
        Args:
            legacy_value: Legacy field value (single string)
            field_type: Type of field ("name" or "text")
            
        Returns:
            Dictionary with translations for all three languages
            
        Examples:
            >>> service = TranslationService()
            >>> service.handle_legacy_input("Mathematics", "name")
            {'name_en': 'Mathematics', 'name_uz': 'Mathematics', 'name_ru': 'Mathematics'}
            
            >>> service.handle_legacy_input("What is 2+2?", "text")
            {'text_en': 'What is 2+2?', 'text_uz': 'What is 2+2?', 'text_ru': 'What is 2+2?'}
        """
        if not legacy_value or not isinstance(legacy_value, str):
            legacy_value = ""
        
        # Create multi-language dictionary
        if field_type == "name":
            return {
                "name_en": legacy_value,
                "name_uz": legacy_value,
                "name_ru": legacy_value
            }
        elif field_type == "text":
            return {
                "text_en": legacy_value,
                "text_uz": legacy_value,
                "text_ru": legacy_value
            }
        else:
            raise ValidationError(f"Invalid field_type: {field_type}. Must be 'name' or 'text'")
    
    def _get_language_name(self, language_code: str) -> str:
        """Get human-readable language name from code.
        
        Args:
            language_code: Language code (en, uz, ru)
            
        Returns:
            Human-readable language name
        """
        language_names = {
            "en": "English",
            "uz": "Uzbek",
            "ru": "Russian"
        }
        return language_names.get(language_code, language_code.upper())
