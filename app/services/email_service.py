"""
Email service for sending verification emails.

This module provides async email sending functionality using aiosmtplib
with support for multi-language email content (EN/RU/UZ).
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


class EmailService:
    """
    Service for sending emails via SMTP.
    
    Supports multi-language email content for English, Russian, and Uzbek.
    Uses aiosmtplib for async SMTP operations.
    """
    
    def __init__(self) -> None:
        """Initialize the email service with SMTP configuration from settings."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_from_email = settings.smtp_from_email
        self.frontend_url = settings.frontend_url
    
    def _get_email_content(self, language: str, verification_link: str) -> tuple[str, str]:
        """
        Get localized email subject and body.
        
        Args:
            language: Language code ("en", "ru", or "uz")
            verification_link: The verification URL to include in the email
        
        Returns:
            A tuple of (subject, body) with localized content
        """
        content = {
            "en": {
                "subject": "Verify Your Email - Quiz Auth Module",
                "body": f"""
Hello!

Thank you for registering with Quiz Auth Module.

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
Quiz Auth Module Team
"""
            },
            "ru": {
                "subject": "Подтвердите ваш email - Quiz Auth Module",
                "body": f"""
Здравствуйте!

Спасибо за регистрацию в Quiz Auth Module.

Пожалуйста, подтвердите ваш адрес электронной почты, перейдя по ссылке ниже:

{verification_link}

Эта ссылка действительна в течение 24 часов.

Если вы не создавали учетную запись, пожалуйста, проигнорируйте это письмо.

С уважением,
Команда Quiz Auth Module
"""
            },
            "uz": {
                "subject": "Emailingizni tasdiqlang - Quiz Auth Module",
                "body": f"""
Salom!

Quiz Auth Module'da ro'yxatdan o'tganingiz uchun rahmat.

Iltimos, quyidagi havolani bosib email manzilingizni tasdiqlang:

{verification_link}

Bu havola 24 soat davomida amal qiladi.

Agar siz hisob yaratmagan bo'lsangiz, iltimos, bu xatni e'tiborsiz qoldiring.

Hurmat bilan,
Quiz Auth Module jamoasi
"""
            }
        }
        
        # Default to English if language not supported
        lang = language if language in content else "en"
        return content[lang]["subject"], content[lang]["body"]
    
    async def send_verification_email(
        self,
        email: str,
        verification_token: str,
        language: str = "en"
    ) -> None:
        """
        Send an email verification link to the user.
        
        Creates a verification URL with the token and sends it to the user's
        email address. The email content is localized based on the language parameter.
        
        The email sends a link to the frontend verify page. The frontend will extract
        the token from the URL, call the backend API to verify it, and handle the
        verification response and redirect.
        
        Args:
            email: The recipient's email address
            verification_token: The JWT verification token
            language: Language code for email content ("en", "ru", or "uz")
        
        Raises:
            EmailSendError: If the email fails to send due to SMTP errors
        
        Example:
            >>> email_service = EmailService()
            >>> await email_service.send_verification_email(
            ...     email="user@example.com",
            ...     verification_token="eyJhbGc...",
            ...     language="en"
            ... )
        """
        from app.core.exceptions import EmailSendError
        
        # Construct verification link to frontend verify page
        verification_link = f"{self.frontend_url}/verify?token={verification_token}"
        
        # Get localized content
        subject, body = self._get_email_content(language, verification_link)
        
        # Create message
        message = MIMEMultipart()
        message["From"] = self.smtp_from_email
        message["To"] = email
        message["Subject"] = subject
        
        # Attach body as plain text
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        try:
            # Send email using aiosmtplib
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
        except aiosmtplib.SMTPException as e:
            raise EmailSendError(f"Failed to send verification email: {str(e)}")
        except Exception as e:
            raise EmailSendError(f"Unexpected error sending email: {str(e)}")
