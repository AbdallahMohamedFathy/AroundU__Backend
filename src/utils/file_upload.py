"""
File upload utilities for handling image uploads
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import shutil
from src.core.config import settings


def validate_image(file: UploadFile) -> bool:
    """
    Validate if uploaded file is a valid image.

    Args:
        file: Uploaded file

    Returns:
        True if valid image

    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    allowed = settings.ALLOWED_EXTENSIONS
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed)}"
        )

    # Check file size
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )

    return True


async def save_upload_file(file: UploadFile, subfolder: str = "") -> str:
    """
    Save uploaded file to disk and return the file path.

    Args:
        file: Uploaded file
        subfolder: Optional subfolder within uploads directory

    Returns:
        Relative file path (for storing in database)

    Raises:
        HTTPException: If file cannot be saved
    """
    # Validate file
    validate_image(file)

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_FOLDER)
    if subfolder:
        upload_dir = upload_dir / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = file.filename.split('.')[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = upload_dir / unique_filename

    try:
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verify it's a valid image by opening it
        try:
            with Image.open(file_path) as img:
                # Optionally resize large images
                max_dimension = 2048
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    img.save(file_path)
        except Exception as e:
            # Delete file if it's not a valid image
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )

        # Return relative path
        if subfolder:
            return f"{subfolder}/{unique_filename}"
        return unique_filename

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.

    Args:
        file_path: Relative file path

    Returns:
        True if file deleted successfully
    """
    try:
        full_path = Path(settings.UPLOAD_FOLDER) / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_url(file_path: str, request) -> str:
    """
    Generate full URL for a file.

    Args:
        file_path: Relative file path
        request: FastAPI request object

    Returns:
        Full URL to the file
    """
    base_url = str(request.base_url).rstrip('/')
    return f"{base_url}/uploads/{file_path}"
