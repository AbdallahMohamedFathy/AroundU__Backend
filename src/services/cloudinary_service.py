import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
from src.core.config import settings
from src.core.exceptions import APIException
from fastapi import status
import uuid

# Configure Cloudinary
try:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
except Exception as e:
    pass # Configuration might fail if variables are not yet loaded, but should be handled by pydantic settings

def upload_image(file: UploadFile, folder: str = "places") -> str:
    \"\"\"
    Upload an image to Cloudinary and return the secure URL.
    \"\"\"
    try:
        # We can pass the file.file (which is a SpooledTemporaryFile) directly to cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            folder=f"aroundu/{folder}",
            public_id=f"{folder}_{uuid.uuid4().hex}"
        )
        return result.get("secure_url")
    except Exception as e:
        raise APIException(f"Failed to upload image: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

def delete_image(image_url: str) -> None:
    \"\"\"
    Delete an image from Cloudinary given its secure URL.
    \"\"\"
    try:
        # Extract public_id from the URL
        # Example URL: https://res.cloudinary.com/dvecsfbmu/image/upload/v1234567890/aroundu/places/places_12345.jpg
        # The public_id is everything after the upload/[version]/ and before the extension
        
        if "cloudinary.com" not in image_url:
            return # Not a cloudinary image, skip
            
        parts = image_url.split("/")
        # Find 'upload', then skip the version (v...) and join the rest, minus extension
        if "upload" in parts:
            upload_idx = parts.index("upload")
            
            # The structure is usually /upload/v123456789/folder/subfolder/file.img
            # Sometimes there is no version.
            path_parts = parts[upload_idx+1:]
            
            # Remove version if it exists (starts with 'v' and followed by numbers)
            if path_parts[0].startswith('v') and path_parts[0][1:].isdigit():
                path_parts = path_parts[1:]
                
            public_id_with_ext = "/".join(path_parts)
            public_id = public_id_with_ext.rsplit(".", 1)[0]
            
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        # Log error in extreme cases, but don't crash since deletion shouldn't fail the whole user flow
        pass
