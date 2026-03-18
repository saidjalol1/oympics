"""
Translation dictionaries for multi-language support.

This module provides translations for all user-facing messages in English,
Russian, and Uzbek languages. It includes error messages, success messages,
and welcome page content.

Supported languages:
- en: English
- ru: Russian (Русский)
- uz: Uzbek (O'zbek)
"""

from typing import Dict


# English translations
TRANSLATIONS_EN: Dict[str, str] = {
    # Success messages
    "registration_success": "Registration successful. Please check your email to verify your account.",
    "verification_success": "Email verified successfully. You are now logged in.",
    "login_success": "Login successful.",
    "logout_success": "Logged out successfully.",
    "token_refresh_success": "Token refreshed successfully.",
    
    # Error messages - Validation
    "invalid_email": "Invalid email format.",
    "password_too_short": "Password must be at least 8 characters long.",
    "missing_fields": "Required fields are missing.",
    "invalid_request": "Invalid request format.",
    
    # Error messages - Authentication
    "invalid_credentials": "Invalid email or password.",
    "invalid_token": "Invalid or malformed token.",
    "expired_token": "Token has expired.",
    "missing_token": "Authentication token is missing.",
    "authentication_required": "Authentication is required.",
    
    # Error messages - Authorization
    "email_not_verified": "Please verify your email address before logging in.",
    "insufficient_permissions": "You do not have permission to perform this action.",
    
    # Error messages - Resources
    "user_not_found": "User not found.",
    "email_already_exists": "An account with this email already exists.",
    
    # Error messages - Service
    "email_send_error": "Failed to send verification email. Please try again later.",
    "internal_error": "An internal error occurred. Please try again later.",
    "service_unavailable": "Service is temporarily unavailable. Please try again later.",
    
    # Welcome page content
    "welcome_title": "Quiz Authentication Module",
    "welcome_heading": "Welcome to Quiz Authentication Module",
    "welcome_description": "This is a secure authentication system with multi-language support for quiz applications.",
    "welcome_features_title": "Features",
    "welcome_feature_registration": "User registration with email verification",
    "welcome_feature_login": "Secure login and logout",
    "welcome_feature_tokens": "Token-based authentication",
    "welcome_feature_multilang": "Multi-language support (EN/RU/UZ)",
    "welcome_api_docs_title": "API Documentation",
    "welcome_swagger_link": "Swagger UI",
    "welcome_redoc_link": "ReDoc",
    "welcome_language_label": "Language:",
}

# Russian translations
TRANSLATIONS_RU: Dict[str, str] = {
    # Success messages
    "registration_success": "Регистрация успешна. Пожалуйста, проверьте свою электронную почту для подтверждения аккаунта.",
    "verification_success": "Email успешно подтвержден. Вы вошли в систему.",
    "login_success": "Вход выполнен успешно.",
    "logout_success": "Выход выполнен успешно.",
    "token_refresh_success": "Токен успешно обновлен.",
    
    # Error messages - Validation
    "invalid_email": "Неверный формат электронной почты.",
    "password_too_short": "Пароль должен содержать не менее 8 символов.",
    "missing_fields": "Отсутствуют обязательные поля.",
    "invalid_request": "Неверный формат запроса.",
    
    # Error messages - Authentication
    "invalid_credentials": "Неверный email или пароль.",
    "invalid_token": "Недействительный или неправильный токен.",
    "expired_token": "Срок действия токена истек.",
    "missing_token": "Отсутствует токен аутентификации.",
    "authentication_required": "Требуется аутентификация.",
    
    # Error messages - Authorization
    "email_not_verified": "Пожалуйста, подтвердите свой email перед входом в систему.",
    "insufficient_permissions": "У вас нет прав для выполнения этого действия.",
    
    # Error messages - Resources
    "user_not_found": "Пользователь не найден.",
    "email_already_exists": "Аккаунт с этим email уже существует.",
    
    # Error messages - Service
    "email_send_error": "Не удалось отправить письмо для подтверждения. Пожалуйста, попробуйте позже.",
    "internal_error": "Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.",
    "service_unavailable": "Сервис временно недоступен. Пожалуйста, попробуйте позже.",
    
    # Welcome page content
    "welcome_title": "Модуль Аутентификации для Викторин",
    "welcome_heading": "Добро пожаловать в Модуль Аутентификации для Викторин",
    "welcome_description": "Это безопасная система аутентификации с поддержкой нескольких языков для приложений викторин.",
    "welcome_features_title": "Возможности",
    "welcome_feature_registration": "Регистрация пользователей с подтверждением email",
    "welcome_feature_login": "Безопасный вход и выход",
    "welcome_feature_tokens": "Аутентификация на основе токенов",
    "welcome_feature_multilang": "Поддержка нескольких языков (EN/RU/UZ)",
    "welcome_api_docs_title": "Документация API",
    "welcome_swagger_link": "Swagger UI",
    "welcome_redoc_link": "ReDoc",
    "welcome_language_label": "Язык:",
}

# Uzbek translations
TRANSLATIONS_UZ: Dict[str, str] = {
    # Success messages
    "registration_success": "Ro'yxatdan o'tish muvaffaqiyatli. Hisobingizni tasdiqlash uchun emailingizni tekshiring.",
    "verification_success": "Email muvaffaqiyatli tasdiqlandi. Siz tizimga kirdingiz.",
    "login_success": "Tizimga kirish muvaffaqiyatli.",
    "logout_success": "Tizimdan chiqish muvaffaqiyatli.",
    "token_refresh_success": "Token muvaffaqiyatli yangilandi.",
    
    # Error messages - Validation
    "invalid_email": "Noto'g'ri email formati.",
    "password_too_short": "Parol kamida 8 ta belgidan iborat bo'lishi kerak.",
    "missing_fields": "Majburiy maydonlar to'ldirilmagan.",
    "invalid_request": "Noto'g'ri so'rov formati.",
    
    # Error messages - Authentication
    "invalid_credentials": "Noto'g'ri email yoki parol.",
    "invalid_token": "Noto'g'ri yoki buzilgan token.",
    "expired_token": "Token muddati tugagan.",
    "missing_token": "Autentifikatsiya tokeni yo'q.",
    "authentication_required": "Autentifikatsiya talab qilinadi.",
    
    # Error messages - Authorization
    "email_not_verified": "Tizimga kirishdan oldin emailingizni tasdiqlang.",
    "insufficient_permissions": "Sizda bu amalni bajarish uchun ruxsat yo'q.",
    
    # Error messages - Resources
    "user_not_found": "Foydalanuvchi topilmadi.",
    "email_already_exists": "Bu email bilan hisob allaqachon mavjud.",
    
    # Error messages - Service
    "email_send_error": "Tasdiqlash emailini yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
    "internal_error": "Ichki xatolik yuz berdi. Keyinroq qayta urinib ko'ring.",
    "service_unavailable": "Xizmat vaqtincha mavjud emas. Keyinroq qayta urinib ko'ring.",
    
    # Welcome page content
    "welcome_title": "Viktorina Autentifikatsiya Moduli",
    "welcome_heading": "Viktorina Autentifikatsiya Moduliga Xush Kelibsiz",
    "welcome_description": "Bu viktorina ilovalari uchun ko'p tilli qo'llab-quvvatlanadigan xavfsiz autentifikatsiya tizimi.",
    "welcome_features_title": "Imkoniyatlar",
    "welcome_feature_registration": "Email tasdiqlash bilan foydalanuvchi ro'yxatdan o'tishi",
    "welcome_feature_login": "Xavfsiz kirish va chiqish",
    "welcome_feature_tokens": "Token asosida autentifikatsiya",
    "welcome_feature_multilang": "Ko'p tilli qo'llab-quvvatlash (EN/RU/UZ)",
    "welcome_api_docs_title": "API Hujjatlari",
    "welcome_swagger_link": "Swagger UI",
    "welcome_redoc_link": "ReDoc",
    "welcome_language_label": "Til:",
}


class TranslationManager:
    """
    Manages translations for multiple languages.
    
    This class provides methods to retrieve translated messages based on
    language codes. It supports English (en), Russian (ru), and Uzbek (uz).
    """
    
    def __init__(self) -> None:
        """Initialize the translation manager with all language dictionaries."""
        self.translations: Dict[str, Dict[str, str]] = {
            "en": TRANSLATIONS_EN,
            "ru": TRANSLATIONS_RU,
            "uz": TRANSLATIONS_UZ,
        }
        self.default_language = "en"
    
    def get(self, key: str, language: str = "en") -> str:
        """
        Get a translated message by key and language.
        
        Args:
            key: The translation key (e.g., "login_success")
            language: The language code ("en", "ru", or "uz")
        
        Returns:
            The translated message string. If the key or language is not found,
            returns the key itself as a fallback.
        
        Examples:
            >>> tm = TranslationManager()
            >>> tm.get("login_success", "en")
            'Login successful.'
            >>> tm.get("login_success", "ru")
            'Вход выполнен успешно.'
        """
        # Normalize language code to lowercase
        language = language.lower()
        
        # Get the language dictionary, fallback to default if not found
        lang_dict = self.translations.get(language, self.translations[self.default_language])
        
        # Get the translation, fallback to key if not found
        return lang_dict.get(key, key)
    
    def get_all(self, language: str = "en") -> Dict[str, str]:
        """
        Get all translations for a specific language.
        
        Args:
            language: The language code ("en", "ru", or "uz")
        
        Returns:
            A dictionary containing all translations for the specified language.
            If the language is not found, returns English translations.
        
        Examples:
            >>> tm = TranslationManager()
            >>> translations = tm.get_all("en")
            >>> "login_success" in translations
            True
        """
        # Normalize language code to lowercase
        language = language.lower()
        
        # Return the language dictionary, fallback to default if not found
        return self.translations.get(language, self.translations[self.default_language])


# Create a global instance for easy import
translations = TranslationManager()
