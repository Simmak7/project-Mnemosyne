"""
FastAPI router for Albums feature.

Endpoints:
- POST   /albums/                    - Create album
- GET    /albums/                    - List user's albums
- GET    /albums/{id}                - Get album with images
- PUT    /albums/{id}                - Update album
- DELETE /albums/{id}                - Delete album
- POST   /albums/{id}/images         - Add images to album
- DELETE /albums/{id}/images         - Remove images from album
- GET    /albums/{id}/images         - Get album images (paginated)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_active_user
import models
from .service import AlbumService
from .schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumWithImagesResponse,
    AlbumListResponse,
    AlbumImageResponse,
    AddImagesToAlbum,
    RemoveImagesFromAlbum
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/albums", tags=["albums"])


@router.post("/", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    album_data: AlbumCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new album."""
    try:
        album = AlbumService.create_album(
            db=db,
            owner_id=current_user.id,
            name=album_data.name,
            description=album_data.description
        )
        return AlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            cover_image_id=album.cover_image_id,
            image_count=0,
            created_at=album.created_at,
            updated_at=album.updated_at,
            cover_image=None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=AlbumListResponse)
def list_albums(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all albums for the current user."""
    albums = AlbumService.get_albums_by_user(db, current_user.id, skip, limit)

    album_responses = []
    for album in albums:
        image_count = AlbumService.get_album_image_count(db, album.id)
        cover_image = None
        if album.cover_image:
            cover_image = AlbumImageResponse(
                id=album.cover_image.id,
                filename=album.cover_image.filename,
                blur_hash=album.cover_image.blur_hash,
                width=album.cover_image.width,
                height=album.cover_image.height
            )

        album_responses.append(AlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            cover_image_id=album.cover_image_id,
            image_count=image_count,
            created_at=album.created_at,
            updated_at=album.updated_at,
            cover_image=cover_image
        ))

    return AlbumListResponse(albums=album_responses, total=len(album_responses))


@router.get("/{album_id}", response_model=AlbumWithImagesResponse)
def get_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get an album with its images."""
    album = AlbumService.get_album(db, album_id, current_user.id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Filter out trashed images
    images = [img for img in album.images if not img.is_trashed]

    return AlbumWithImagesResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_id=album.cover_image_id,
        image_count=len(images),
        created_at=album.created_at,
        updated_at=album.updated_at,
        images=[
            AlbumImageResponse(
                id=img.id,
                filename=img.filename,
                blur_hash=img.blur_hash,
                width=img.width,
                height=img.height
            )
            for img in images
        ]
    )


@router.put("/{album_id}", response_model=AlbumResponse)
def update_album(
    album_id: int,
    album_data: AlbumUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update an album's details."""
    try:
        album = AlbumService.update_album(
            db=db,
            album_id=album_id,
            owner_id=current_user.id,
            name=album_data.name,
            description=album_data.description,
            cover_image_id=album_data.cover_image_id
        )
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")

        image_count = AlbumService.get_album_image_count(db, album.id)

        return AlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            cover_image_id=album.cover_image_id,
            image_count=image_count,
            created_at=album.created_at,
            updated_at=album.updated_at,
            cover_image=None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete an album (does not delete the images)."""
    try:
        deleted = AlbumService.delete_album(db, album_id, current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Album not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{album_id}/images")
def add_images_to_album(
    album_id: int,
    data: AddImagesToAlbum,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Add images to an album."""
    try:
        added = AlbumService.add_images_to_album(
            db=db,
            album_id=album_id,
            owner_id=current_user.id,
            image_ids=data.image_ids
        )
        return {"added": added, "message": f"Added {added} images to album"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{album_id}/images")
def remove_images_from_album(
    album_id: int,
    data: RemoveImagesFromAlbum,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Remove images from an album."""
    try:
        removed = AlbumService.remove_images_from_album(
            db=db,
            album_id=album_id,
            owner_id=current_user.id,
            image_ids=data.image_ids
        )
        return {"removed": removed, "message": f"Removed {removed} images from album"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{album_id}/images")
def get_album_images(
    album_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get images in an album (paginated)."""
    from features.images.schemas import ImageResponse

    images = AlbumService.get_album_images(
        db=db,
        album_id=album_id,
        owner_id=current_user.id,
        skip=skip,
        limit=limit
    )

    # Convert to ImageResponse format for consistency with gallery
    return [
        ImageResponse(
            id=img.id,
            filename=img.filename,
            filepath=img.filepath,
            prompt=img.prompt,
            ai_analysis_status=img.ai_analysis_status,
            ai_analysis_result=img.ai_analysis_result,
            uploaded_at=img.uploaded_at,
            blur_hash=img.blur_hash,
            width=img.width,
            height=img.height,
            is_favorite=img.is_favorite,
            is_trashed=img.is_trashed,
            trashed_at=img.trashed_at,
            tags=[{"id": t.id, "name": t.name} for t in img.tags]
        )
        for img in images
    ]
