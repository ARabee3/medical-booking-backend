"""Cloudinary helper functions for image upload and deletion."""

import cloudinary
import cloudinary.uploader
from django.conf import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY["cloud_name"],
    api_key=settings.CLOUDINARY["api_key"],
    api_secret=settings.CLOUDINARY["api_secret"],
)


def upload_to_cloudinary(file, folder="doctor_images"):
    """Upload a file to Cloudinary and return (secure_url, public_id)."""
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="image",
    )
    return result["secure_url"], result["public_id"]


def delete_from_cloudinary(public_id):
    """Delete an image from Cloudinary by its public_id."""
    if public_id:
        cloudinary.uploader.destroy(public_id)
