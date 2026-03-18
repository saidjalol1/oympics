"""Unit tests for ImageService.

Tests image validation, optimization, and storage functionality.
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi import UploadFile
from unittest.mock import Mock

from app.services.image_service import ImageService
from app.core.exceptions import ValidationError


@pytest.fixture
def image_service():
    """Create an ImageService instance with mocked repository."""
    mock_repo = Mock()
    return ImageService(mock_repo)


def create_test_image(width: int, height: int, format: str = "JPEG") -> BytesIO:
    """Create a test image in memory.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (JPEG, PNG, WEBP)
        
    Returns:
        BytesIO object containing the image data
    """
    image = Image.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def create_upload_file(
    content: BytesIO, 
    filename: str, 
    content_type: str
) -> UploadFile:
    """Create a FastAPI UploadFile from BytesIO content.
    
    Args:
        content: BytesIO object with file content
        filename: Original filename
        content_type: MIME type
        
    Returns:
        UploadFile instance
    """
    return UploadFile(
        file=content,
        filename=filename,
        headers={"content-type": content_type}
    )


class TestImageValidation:
    """Test image validation methods."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_jpeg(self, image_service):
        """Test validation of a valid JPEG image."""
        # Create a valid JPEG image
        image_data = create_test_image(800, 600, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "test.jpg", 
            "image/jpeg"
        )
        
        # Should not raise an exception
        width, height = await image_service.validate_image(upload_file)
        assert width == 800
        assert height == 600
    
    @pytest.mark.asyncio
    async def test_validate_valid_png(self, image_service):
        """Test validation of a valid PNG image."""
        # Create a valid PNG image
        image_data = create_test_image(1024, 768, "PNG")
        upload_file = create_upload_file(
            image_data, 
            "test.png", 
            "image/png"
        )
        
        # Should not raise an exception
        width, height = await image_service.validate_image(upload_file)
        assert width == 1024
        assert height == 768
    
    @pytest.mark.asyncio
    async def test_validate_image_too_small(self, image_service):
        """Test validation fails for images smaller than MIN_DIMENSION."""
        # Create an image that's too small
        image_data = create_test_image(50, 50, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "small.jpg", 
            "image/jpeg"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await image_service.validate_image(upload_file)
        
        assert "at least" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_validate_image_too_large(self, image_service):
        """Test validation fails for images larger than MAX_DIMENSION."""
        # Create an image that's too large
        image_data = create_test_image(5000, 5000, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "large.jpg", 
            "image/jpeg"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await image_service.validate_image(upload_file)
        
        assert "exceed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_validate_unsupported_format(self, image_service):
        """Test validation fails for unsupported image formats."""
        # Create a file with unsupported content type
        image_data = create_test_image(800, 600, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "test.gif", 
            "image/gif"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await image_service.validate_image(upload_file)
        
        assert "unsupported" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_validate_empty_file(self, image_service):
        """Test validation fails for empty files."""
        # Create an empty file
        empty_data = BytesIO(b"")
        upload_file = create_upload_file(
            empty_data, 
            "empty.jpg", 
            "image/jpeg"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await image_service.validate_image(upload_file)
        
        assert "empty" in str(exc_info.value).lower()


class TestImageOptimization:
    """Test image optimization methods."""
    
    @pytest.mark.asyncio
    async def test_optimize_image_no_resize(self, image_service):
        """Test optimization without resizing (image within MAX_WIDTH)."""
        # Create an image that doesn't need resizing
        width, height = 1200, 800
        image_data = create_test_image(width, height, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "test.jpg", 
            "image/jpeg"
        )
        
        # Optimize
        optimized_bytes, new_width, new_height = await image_service.optimize_image(
            upload_file, width, height
        )
        
        # Dimensions should remain the same
        assert new_width == width
        assert new_height == height
        assert len(optimized_bytes) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_image_with_resize(self, image_service):
        """Test optimization with resizing (image exceeds MAX_WIDTH)."""
        # Create an image that needs resizing
        width, height = 2400, 1600
        image_data = create_test_image(width, height, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "large.jpg", 
            "image/jpeg"
        )
        
        # Optimize
        optimized_bytes, new_width, new_height = await image_service.optimize_image(
            upload_file, width, height
        )
        
        # Should be resized to MAX_WIDTH
        assert new_width == image_service.MAX_WIDTH
        # Aspect ratio should be maintained
        expected_height = int(height * (image_service.MAX_WIDTH / width))
        assert new_height == expected_height
        assert len(optimized_bytes) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_converts_to_webp(self, image_service):
        """Test that optimization converts images to WebP format."""
        # Create a JPEG image
        width, height = 800, 600
        image_data = create_test_image(width, height, "JPEG")
        upload_file = create_upload_file(
            image_data, 
            "test.jpg", 
            "image/jpeg"
        )
        
        # Optimize
        optimized_bytes, _, _ = await image_service.optimize_image(
            upload_file, width, height
        )
        
        # Verify it's WebP format
        optimized_image = Image.open(BytesIO(optimized_bytes))
        assert optimized_image.format == "WEBP"


class TestImageConstants:
    """Test that ImageService constants match requirements."""
    
    def test_constants_match_requirements(self):
        """Verify ImageService constants match the specification."""
        assert ImageService.MAX_FILE_SIZE == 5242880  # 5MB in bytes
        assert ImageService.ALLOWED_FORMATS == [
            "image/jpeg", "image/png", "image/webp"
        ]
        assert ImageService.MIN_DIMENSION == 100
        assert ImageService.MAX_DIMENSION == 4000
        assert ImageService.MAX_WIDTH == 1920
