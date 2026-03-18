"""Image service for question image validation, optimization, and storage.

This module provides the ImageService class for handling image uploads,
validation, optimization, and storage for question images.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple
from datetime import datetime
from PIL import Image
from fastapi import UploadFile

from app.core.exceptions import ValidationError
from app.models.question_image import QuestionImage
from app.repositories.image_repository import ImageRepository


class ImageService:
    """Service for handling image uploads and management.
    
    Provides methods for validating image files, optimizing images for web delivery,
    storing images to the filesystem, and managing image metadata in the database.
    
    Constants:
        MAX_FILE_SIZE: Maximum allowed file size in bytes (5MB)
        ALLOWED_FORMATS: List of allowed MIME types
        MIN_DIMENSION: Minimum image dimension in pixels
        MAX_DIMENSION: Maximum image dimension in pixels
        MAX_WIDTH: Maximum width for optimization (images wider than this are resized)
    
    Attributes:
        image_repo: ImageRepository instance for database operations
    """
    
    # Constants
    MAX_FILE_SIZE = 5242880  # 5MB in bytes
    ALLOWED_FORMATS = ["image/jpeg", "image/png", "image/webp"]
    MIN_DIMENSION = 100  # pixels
    MAX_DIMENSION = 4000  # pixels
    MAX_WIDTH = 1920  # pixels for optimization
    
    UPLOAD_DIR = "uploads/questions"
    COMPRESSION_QUALITY = 85
    
    def __init__(self, image_repo: ImageRepository):
        """Initialize ImageService with image repository.
        
        Args:
            image_repo: ImageRepository instance for database operations
        """
        self.image_repo = image_repo
    
    async def validate_image(self, file: UploadFile) -> Tuple[int, int]:
        """Validate image file for size, format, and dimensions.
        
        Validates that the uploaded file:
        - Does not exceed MAX_FILE_SIZE
        - Has an allowed MIME type (JPEG, PNG, or WebP)
        - Has valid image format by checking file header
        - Has dimensions within MIN_DIMENSION and MAX_DIMENSION range
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            Tuple of (width, height) in pixels
            
        Raises:
            ValidationError: If validation fails for any reason
            
        Examples:
            >>> service = ImageService(image_repo)
            >>> width, height = await service.validate_image(uploaded_file)
            >>> print(f"Image dimensions: {width}x{height}")
        """
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / 1024 / 1024
            raise ValidationError(
                f"Image file size exceeds maximum allowed size of {max_size_mb}MB"
            )
        
        if file_size == 0:
            raise ValidationError("Image file is empty")
        
        # Check MIME type
        content_type = file.content_type
        if content_type not in self.ALLOWED_FORMATS:
            raise ValidationError(
                f"Unsupported image format '{content_type}'. "
                f"Allowed formats: JPEG, PNG, WebP"
            )
        
        # Validate image format and dimensions by opening with PIL
        try:
            image = Image.open(file.file)
            
            # Verify the image format matches the content type
            format_map = {
                "image/jpeg": "JPEG",
                "image/png": "PNG",
                "image/webp": "WEBP"
            }
            expected_format = format_map.get(content_type)
            if image.format != expected_format:
                raise ValidationError(
                    f"Image file header does not match content type. "
                    f"Expected {expected_format}, got {image.format}"
                )
            
            width, height = image.size
            
            # Validate dimensions
            if width < self.MIN_DIMENSION or height < self.MIN_DIMENSION:
                raise ValidationError(
                    f"Image dimensions must be at least "
                    f"{self.MIN_DIMENSION}x{self.MIN_DIMENSION} pixels. "
                    f"Got {width}x{height} pixels"
                )
            
            if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                raise ValidationError(
                    f"Image dimensions must not exceed "
                    f"{self.MAX_DIMENSION}x{self.MAX_DIMENSION} pixels. "
                    f"Got {width}x{height} pixels"
                )
            
            file.file.seek(0)  # Reset for later use
            return width, height
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid image file: {str(e)}")
    
    async def optimize_image(
        self, 
        file: UploadFile, 
        width: int, 
        height: int
    ) -> Tuple[bytes, int, int]:
        """Optimize image for web delivery.
        
        Optimizes the image by:
        - Resizing if width exceeds MAX_WIDTH (maintaining aspect ratio)
        - Converting to WebP format for better compression
        - Compressing with quality setting
        
        Args:
            file: Uploaded file to optimize
            width: Original image width in pixels
            height: Original image height in pixels
            
        Returns:
            Tuple of (optimized_bytes, new_width, new_height)
            
        Raises:
            ValidationError: If optimization fails
            
        Examples:
            >>> service = ImageService(image_repo)
            >>> optimized_data, new_w, new_h = await service.optimize_image(
            ...     file, 2400, 1600
            ... )
            >>> print(f"Resized from 2400x1600 to {new_w}x{new_h}")
        """
        try:
            image = Image.open(file.file)
            
            # Resize if too large
            if width > self.MAX_WIDTH:
                ratio = self.MAX_WIDTH / width
                new_width = self.MAX_WIDTH
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                new_width = width
                new_height = height
            
            # Convert to RGB if necessary (for WebP compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                
                # Convert palette images to RGBA first
                if image.mode == 'P':
                    image = image.convert('RGBA')
                
                # Paste image on background using alpha channel as mask
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as WebP
            from io import BytesIO
            output = BytesIO()
            image.save(
                output, 
                format='WEBP', 
                quality=self.COMPRESSION_QUALITY, 
                method=6  # Slowest but best compression
            )
            optimized_bytes = output.getvalue()
            
            return optimized_bytes, new_width, new_height
            
        except Exception as e:
            raise ValidationError(f"Failed to optimize image: {str(e)}")
    
    async def save_image(
        self, 
        question_id: int, 
        file: UploadFile, 
        order: int
    ) -> QuestionImage:
        """Save image to filesystem and database.
        
        Performs the following operations:
        1. Validates the question doesn't already have 2 images
        2. Validates the image order is not already taken
        3. Validates the image file
        4. Optimizes the image
        5. Generates a unique filename
        6. Creates directory structure if needed
        7. Saves the file to disk
        8. Saves metadata to database
        
        Args:
            question_id: Question ID to attach image to
            file: Uploaded file
            order: Image order (1 or 2)
            
        Returns:
            Created QuestionImage instance
            
        Raises:
            ValidationError: If validation fails or limit exceeded
            
        Examples:
            >>> service = ImageService(image_repo)
            >>> image = await service.save_image(
            ...     question_id=1, file=uploaded_file, order=1
            ... )
            >>> print(f"Image saved: {image.image_path}")
        """
        # Validate order
        if order not in (1, 2):
            raise ValidationError("Image order must be 1 or 2")
        
        # Check if question already has 2 images
        existing_images = await self.image_repo.get_by_question_id(question_id)
        if len(existing_images) >= 2:
            raise ValidationError("Question already has maximum of 2 images")
        
        # Check if order is already taken
        if any(img.image_order == order for img in existing_images):
            raise ValidationError(
                f"Image order {order} is already taken for this question"
            )
        
        # Validate image
        width, height = await self.validate_image(file)
        
        # Optimize image
        optimized_bytes, new_width, new_height = await self.optimize_image(
            file, width, height
        )
        
        # Generate unique filename
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{unique_id}_{timestamp}.webp"
        
        # Create directory structure
        question_dir = Path(self.UPLOAD_DIR) / str(question_id)
        question_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = question_dir / filename
        try:
            with open(file_path, 'wb') as f:
                f.write(optimized_bytes)
        except Exception as e:
            raise ValidationError(f"Failed to save image file: {str(e)}")
        
        # Save to database
        relative_path = f"{self.UPLOAD_DIR}/{question_id}/{filename}"
        try:
            image = await self.image_repo.create(
                question_id=question_id,
                image_path=relative_path,
                image_order=order,
                original_filename=file.filename,
                file_size=len(optimized_bytes),
                width=new_width,
                height=new_height
            )
            return image
        except Exception as e:
            # Clean up file if database operation fails
            if file_path.exists():
                file_path.unlink()
            raise ValidationError(f"Failed to save image metadata: {str(e)}")
    
    async def delete_image(self, image_id: int) -> None:
        """Delete image from filesystem and database.
        
        Deletes the image file from the filesystem and removes the metadata
        from the database. If the file doesn't exist, only the database
        record is removed.
        
        Args:
            image_id: Image ID to delete
            
        Examples:
            >>> service = ImageService(image_repo)
            >>> await service.delete_image(image_id=1)
        """
        image = await self.image_repo.get_by_id(image_id)
        if not image:
            return
        
        # Delete file from filesystem
        file_path = Path(image.image_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log error but continue with database deletion
                print(f"Warning: Failed to delete image file {file_path}: {str(e)}")
        
        # Delete from database
        await self.image_repo.delete(image)
    
    async def delete_question_images(self, question_id: int) -> None:
        """Delete all images for a question.
        
        Deletes all image files and metadata for the specified question.
        Also removes the question's image directory if it exists.
        
        Args:
            question_id: Question ID to delete images for
            
        Examples:
            >>> service = ImageService(image_repo)
            >>> await service.delete_question_images(question_id=1)
        """
        images = await self.image_repo.get_by_question_id(question_id)
        
        # Delete each image
        for image in images:
            await self.delete_image(image.id)
        
        # Delete question directory
        question_dir = Path(self.UPLOAD_DIR) / str(question_id)
        if question_dir.exists() and question_dir.is_dir():
            try:
                shutil.rmtree(question_dir)
            except Exception as e:
                # Log error but don't raise
                print(f"Warning: Failed to delete directory {question_dir}: {str(e)}")
