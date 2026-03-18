"""Question service for business logic and validation.

This module provides the QuestionService class for managing question operations,
including creation, retrieval, updates, and deletion with comprehensive validation.
"""

from typing import Tuple, List, Dict, Optional
from app.models.question import Question
from app.repositories.question_repository import QuestionRepository
from app.repositories.question_option_repository import QuestionOptionRepository
from app.repositories.test_repository import TestRepository
from app.services.translation_service import TranslationService
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError
)


class QuestionService:
    """Service for question business logic and validation.
    
    Handles all question operations including creation, retrieval, updates,
    and deletion with comprehensive validation and error handling.
    """
    
    def __init__(
        self, 
        question_repository: QuestionRepository,
        question_option_repository: QuestionOptionRepository,
        test_repository: TestRepository,
        translation_service: TranslationService
    ):
        """Initialize QuestionService with dependencies.
        
        Args:
            question_repository: QuestionRepository instance for database operations
            question_option_repository: QuestionOptionRepository for option operations
            test_repository: TestRepository instance for test validation
            translation_service: TranslationService instance for multi-language handling
        """
        self.question_repo = question_repository
        self.option_repo = question_option_repository
        self.test_repo = test_repository
        self.translation_service = translation_service
    
    def _validate_text(
        self, 
        text_en: Optional[str] = None,
        text_uz: Optional[str] = None,
        text_ru: Optional[str] = None
    ) -> None:
        """Validate question text for all languages.
        
        Args:
            text_en: Question text in English
            text_uz: Question text in Uzbek
            text_ru: Question text in Russian
            
        Raises:
            ValidationError: If text is invalid
        """
        # Validate individual field lengths
        for lang, value in [("en", text_en), ("uz", text_uz), ("ru", text_ru)]:
            if value is None:
                continue
            
            if not isinstance(value, str):
                raise ValidationError(f"Question text_{lang} must be a string")
            
            if len(value) < 1 or len(value) > 1000:
                raise ValidationError(f"Question text_{lang} must be between 1 and 1000 characters")
            
            if value.strip() != value:
                raise ValidationError(f"Question text_{lang} cannot have leading or trailing whitespace")
    
    def _validate_options(
        self, 
        options: List[Dict[str, str]], 
        correct_answer: str
    ) -> None:
        """Validate question options.
        
        Args:
            options: List of option dictionaries with 'label' and multi-language text keys
            correct_answer: Correct answer label (A-J)
            
        Raises:
            ValidationError: If options are invalid
        """
        if not isinstance(options, list):
            raise ValidationError("Options must be a list")
        
        if len(options) < 3 or len(options) > 10:
            raise ValidationError("Question must have 3 to 10 options")
        
        valid_labels = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'}
        seen_labels = set()
        seen_texts_en = set()
        
        for i, option in enumerate(options):
            if not isinstance(option, dict):
                raise ValidationError(f"Option {i} must be a dictionary")
            
            # Check for required keys (support both legacy and new format)
            has_legacy = 'text' in option
            has_multilang = 'text_en' in option or 'text_uz' in option or 'text_ru' in option
            
            if 'label' not in option:
                raise ValidationError(f"Option {i} must have 'label' key")
            
            if not has_legacy and not has_multilang:
                raise ValidationError(f"Option {i} must have either 'text' or multi-language text keys")
            
            label = option['label']
            
            # Validate label
            if not isinstance(label, str) or label not in valid_labels:
                raise ValidationError(f"Option {i} label must be A-J")
            
            if label in seen_labels:
                raise ValidationError(f"Duplicate option label: {label}")
            seen_labels.add(label)
            
            # Validate text fields (check at least one language if multi-lang)
            if has_multilang:
                # Validate each language field if present
                for lang in ['en', 'uz', 'ru']:
                    text_key = f'text_{lang}'
                    if text_key in option:
                        text = option[text_key]
                        # Treat empty strings as None
                        if text == "":
                            text = None
                            option[text_key] = None
                        
                        if text is not None:
                            if not isinstance(text, str):
                                raise ValidationError(f"Option {i} {text_key} must be a string")
                            if len(text) > 500:
                                raise ValidationError(f"Option {i} {text_key} must not exceed 500 characters")
                
                # Check for duplicate English text (only among non-empty values)
                if 'text_en' in option and option['text_en']:
                    text_en = option['text_en']
                    if text_en in seen_texts_en:
                        raise ValidationError("Duplicate option text")
                    seen_texts_en.add(text_en)
            else:
                # Legacy format validation
                text = option['text']
                if not isinstance(text, str) or not text:
                    raise ValidationError(f"Option {i} text must be a non-empty string")
                if len(text) > 500:
                    raise ValidationError(f"Option {i} text must not exceed 500 characters")
                if text in seen_texts_en:
                    raise ValidationError("Duplicate option text")
                seen_texts_en.add(text)
        
        # Verify correct_answer matches one of the option labels
        if correct_answer not in seen_labels:
            raise ValidationError(
                f"correct_answer '{correct_answer}' must match one of the option labels"
            )
    
    async def create_question(
        self, 
        test_id: int, 
        text_en: Optional[str] = None,
        text_uz: Optional[str] = None,
        text_ru: Optional[str] = None,
        text: Optional[str] = None,
        correct_answer: str = None,
        options: List[Dict[str, str]] = None
    ) -> Question:
        """Create a new question.
        
        Args:
            test_id: Parent test ID
            text_en: Question text in English (optional if using legacy format)
            text_uz: Question text in Uzbek (optional if using legacy format)
            text_ru: Question text in Russian (optional if using legacy format)
            text: Legacy question text (optional, for backward compatibility)
            correct_answer: Correct answer label (A-J)
            options: List of 3-10 option dictionaries with 'label' and 'text' keys
            
        Returns:
            Created Question instance with options
            
        Raises:
            ValidationError: If text, correct_answer, or options are invalid
            ResourceNotFoundError: If test not found
        """
        # Handle legacy input format
        if text and not (text_en or text_uz or text_ru):
            translations = self.translation_service.handle_legacy_input(text, "text")
            text_en = translations["text_en"]
            text_uz = translations["text_uz"]
            text_ru = translations["text_ru"]
        
        # Validate translations
        self.translation_service.validate_translations(
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            field_name="text"
        )
        
        # Validate individual field lengths
        self._validate_text(text_en=text_en, text_uz=text_uz, text_ru=text_ru)
        self._validate_options(options, correct_answer)
        
        # Verify test exists
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise ResourceNotFoundError(f"Test with id {test_id} not found")
        
        # Prepare legacy field
        legacy_text = self.translation_service.prepare_legacy_field(
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru
        )
        
        # Create question
        question = await self.question_repo.create(
            test_id=test_id,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=legacy_text,
            correct_answer=correct_answer
        )
        
        # Create options
        for option in options:
            # Handle both legacy and multi-language format
            if 'text' in option and not ('text_en' in option or 'text_uz' in option or 'text_ru' in option):
                # Legacy format - convert to multi-language
                translations = self.translation_service.handle_legacy_input(option['text'], "text")
                await self.option_repo.create(
                    question_id=question.id,
                    label=option['label'],
                    text_en=translations['text_en'],
                    text_uz=translations['text_uz'],
                    text_ru=translations['text_ru'],
                    text=option['text']
                )
            else:
                # Multi-language format
                text_en = option.get('text_en')
                text_uz = option.get('text_uz')
                text_ru = option.get('text_ru')
                
                # Prepare legacy field
                legacy_text = self.translation_service.prepare_legacy_field(
                    text_en=text_en,
                    text_uz=text_uz,
                    text_ru=text_ru
                )
                
                await self.option_repo.create(
                    question_id=question.id,
                    label=option['label'],
                    text_en=text_en,
                    text_uz=text_uz,
                    text_ru=text_ru,
                    text=legacy_text
                )
        
        # Reload question with options
        question = await self.question_repo.get_by_id(question.id)
        return question
    
    async def get_question(self, question_id: int) -> Question:
        """Retrieve a question by ID.
        
        Args:
            question_id: Question ID to retrieve
            
        Returns:
            Question instance with options
            
        Raises:
            ResourceNotFoundError: If question not found
        """
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError(f"Question with id {question_id} not found")
        
        return question
    
    async def list_questions(
        self, 
        test_id: int,
        skip: int = 0, 
        limit: int = 100,
        search: str = None
    ) -> Tuple[List[Question], int]:
        """List questions for a test with pagination and search.
        
        Args:
            test_id: Parent test ID
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            search: Optional search term to filter by question text
            
        Returns:
            Tuple of (questions, total_count)
            
        Raises:
            ResourceNotFoundError: If test not found
        """
        # Verify test exists
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise ResourceNotFoundError(f"Test with id {test_id} not found")
        
        return await self.question_repo.list_by_test(
            test_id=test_id,
            skip=skip,
            limit=limit,
            search=search
        )
    
    async def update_question(
        self, 
        question_id: int, 
        text_en: Optional[str] = None,
        text_uz: Optional[str] = None,
        text_ru: Optional[str] = None,
        text: Optional[str] = None,
        correct_answer: str = None,
        options: List[Dict[str, str]] = None
    ) -> Question:
        """Update a question.
        
        Args:
            question_id: Question ID to update
            text_en: New question text in English (optional if using legacy format)
            text_uz: New question text in Uzbek (optional if using legacy format)
            text_ru: New question text in Russian (optional if using legacy format)
            text: Legacy question text (optional, for backward compatibility)
            correct_answer: New correct answer label (A-J)
            options: New list of 3-10 option dictionaries
            
        Returns:
            Updated Question instance with options
            
        Raises:
            ValidationError: If text, correct_answer, or options are invalid
            ResourceNotFoundError: If question not found
        """
        # Verify question exists
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError(f"Question with id {question_id} not found")
        
        # Handle legacy input format
        if text and not (text_en or text_uz or text_ru):
            translations = self.translation_service.handle_legacy_input(text, "text")
            text_en = translations["text_en"]
            text_uz = translations["text_uz"]
            text_ru = translations["text_ru"]
        
        # Validate translations
        self.translation_service.validate_translations(
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            field_name="text"
        )
        
        # Validate individual field lengths
        self._validate_text(text_en=text_en, text_uz=text_uz, text_ru=text_ru)
        self._validate_options(options, correct_answer)
        
        # Prepare legacy field
        legacy_text = self.translation_service.prepare_legacy_field(
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru
        )
        
        # Update question
        updated_question = await self.question_repo.update(
            question_id,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=legacy_text,
            correct_answer=correct_answer
        )
        
        # Delete existing options
        existing_options = await self.option_repo.list_by_question(question_id)
        for option in existing_options:
            await self.option_repo.delete(option.id)
        
        # Create new options
        for option in options:
            # Handle both legacy and multi-language format
            if 'text' in option and not ('text_en' in option or 'text_uz' in option or 'text_ru' in option):
                # Legacy format - convert to multi-language
                translations = self.translation_service.handle_legacy_input(option['text'], "text")
                await self.option_repo.create(
                    question_id=question_id,
                    label=option['label'],
                    text_en=translations['text_en'],
                    text_uz=translations['text_uz'],
                    text_ru=translations['text_ru'],
                    text=option['text']
                )
            else:
                # Multi-language format
                text_en = option.get('text_en')
                text_uz = option.get('text_uz')
                text_ru = option.get('text_ru')
                
                # Prepare legacy field
                legacy_text = self.translation_service.prepare_legacy_field(
                    text_en=text_en,
                    text_uz=text_uz,
                    text_ru=text_ru
                )
                
                await self.option_repo.create(
                    question_id=question_id,
                    label=option['label'],
                    text_en=text_en,
                    text_uz=text_uz,
                    text_ru=text_ru,
                    text=legacy_text
                )
        
        # Reload question with new options
        updated_question = await self.question_repo.get_by_id(question_id)
        return updated_question
    
    async def delete_question(self, question_id: int) -> None:
        """Delete a question.
        
        Args:
            question_id: Question ID to delete
            
        Raises:
            ResourceNotFoundError: If question not found
        """
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError(f"Question with id {question_id} not found")
        
        await self.question_repo.delete(question_id)
