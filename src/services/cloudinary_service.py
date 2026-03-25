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
    raise RuntimeError(f"Cloudinary config failed: {e}") 

def upload_image(file: UploadFile, folder: str = "places") -> str:
    try:
        file.file.seek(0)

        result = cloudinary.uploader.upload(
            file.file,
            folder=f"aroundu/{folder}",
            public_id=f"{folder}_{uuid.uuid4().hex}",
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"}
            ]
        )
        return result.get("secure_url")

    except Exception as e:
        raise APIException(f"Failed to upload image: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
def delete_image(image_url: str) -> None:
    try:
        if not image_url or "res.cloudinary.com" not in image_url:
            return

        parts = image_url.split("/")
        if "upload" not in parts:
            return

        upload_idx = parts.index("upload")
        path_parts = parts[upload_idx+1:]

        if path_parts and path_parts[0].startswith('v') and path_parts[0][1:].isdigit():
            path_parts = path_parts[1:]

        public_id_with_ext = "/".join(path_parts)
        public_id = public_id_with_ext.rsplit(".", 1)[0]

        cloudinary.uploader.destroy(public_id)

    except Exception as e:
        print(f"Cloudinary delete failed: {e}")