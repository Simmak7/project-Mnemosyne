from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from fastapi import HTTPException
import logging

import models
import schemas
from core.auth import get_password_hash, verify_password
from wikilink_parser import create_slug

# Initialize logger
logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating user {user.username}: {e}")
        raise HTTPException(status_code=409, detail="User with this username or email already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating user {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password."""
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_user_by_username(db: Session, username: str):
    """Get a user by username."""
    return db.query(models.User).filter(models.User.username == username).first()

def create_image(db: Session, filename: str, filepath: str, prompt: str | None = None, owner_id: int | None = None):
    db_image = models.Image(filename=filename, filepath=filepath, prompt=prompt, owner_id=owner_id)
    db.add(db_image)
    try:
        db.commit()
        db.refresh(db_image)
        return db_image
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating image {filename}: {e}")
        raise HTTPException(status_code=409, detail="Image with this filename already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create image")

def get_image(db: Session, image_id: int):
    return db.query(models.Image).filter(models.Image.id == image_id).first()

def update_image_analysis_result(db: Session, image_id: int, status: str, result: str | None = None):
    db_image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if db_image:
        db_image.ai_analysis_status = status
        db_image.ai_analysis_result = result
        try:
            db.commit()
            db.refresh(db_image)
        except Exception as e:
            db.rollback()
            logger.exception(f"Error updating image {image_id} analysis result: {e}")
            raise HTTPException(status_code=500, detail="Failed to update image analysis")
    return db_image


def update_image_display_name(db: Session, image_id: int, display_name: str):
    """Update the display_name of an image (used for automatic naming from note title)."""
    db_image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if db_image:
        db_image.display_name = display_name
        try:
            db.commit()
            db.refresh(db_image)
        except Exception as e:
            db.rollback()
            logger.exception(f"Error updating image {image_id} display_name: {e}")
            raise
    return db_image

def create_note(db: Session, title: str, content: str, owner_id: int | None = None,
                source: str = 'manual', is_standalone: bool = True):
    """Create a new note with auto-generated slug and extract tags."""
    from wikilink_parser import extract_hashtags
    from tasks_embeddings import generate_note_embedding_task

    # Generate unique slug
    base_slug = create_slug(title)
    slug = base_slug
    counter = 2

    # Check for existing slug and append suffix if needed
    while db.query(models.Note).filter(
        models.Note.slug == slug,
        models.Note.owner_id == owner_id
    ).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_note = models.Note(title=title, content=content, slug=slug, owner_id=owner_id,
                          is_standalone=is_standalone, source=source)
    db.add(db_note)
    try:
        db.commit()
        db.refresh(db_note)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating note '{title}': {e}")
        raise HTTPException(status_code=409, detail="Note with this slug already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating note '{title}': {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")

    # Extract and add tags from content
    if content:
        hashtags = extract_hashtags(content)
        for tag_name in hashtags:
            try:
                tag = get_or_create_tag(db, tag_name, owner_id)
                if tag not in db_note.tags:
                    db_note.tags.append(tag)
            except Exception as e:
                logger.error(f"Error adding tag {tag_name} to note {db_note.id}: {e}", exc_info=True)

        if hashtags:
            try:
                db.commit()
                db.refresh(db_note)
            except Exception as e:
                db.rollback()
                logger.exception(f"Error committing tags for note {db_note.id}: {e}")
                # Don't raise - note already created, tags are optional

    # Trigger embedding generation (async, non-blocking)
    try:
        generate_note_embedding_task.delay(db_note.id)
    except Exception as e:
        logger.error(f"Failed to queue embedding generation for note {db_note.id}: {e}", exc_info=True)

    return db_note

def get_note(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def get_notes_by_user(db: Session, owner_id: int):
    return db.query(models.Note).filter(models.Note.owner_id == owner_id).all()

def add_image_to_note(db: Session, image_id: int, note_id: int):
    db_relation = models.ImageNoteRelation(image_id=image_id, note_id=note_id)
    db.add(db_relation)
    try:
        db.commit()
        db.refresh(db_relation)
        return db_relation
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error linking image {image_id} to note {note_id}: {e}")
        raise HTTPException(status_code=409, detail="Image-note relationship already exists")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error linking image {image_id} to note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to link image to note")

def get_images(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Image).offset(skip).limit(limit).all()

def get_notes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Note).offset(skip).limit(limit).all()


# Tag CRUD operations
def get_or_create_tag(db: Session, tag_name: str, owner_id: Optional[int] = None) -> models.Tag:
    """Get existing tag or create new one (case-insensitive, stored lowercase)."""
    tag_name_lower = tag_name.lower().strip()

    # Try to find existing tag
    tag = db.query(models.Tag).filter(
        models.Tag.name == tag_name_lower,
        models.Tag.owner_id == owner_id
    ).first()

    if tag:
        return tag

    # Create new tag
    tag = models.Tag(name=tag_name_lower, owner_id=owner_id)
    db.add(tag)
    try:
        db.commit()
        db.refresh(tag)
        return tag
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating tag '{tag_name}': {e}")
        # Try to fetch again - might have been created by concurrent request
        tag = db.query(models.Tag).filter(
            models.Tag.name == tag_name_lower,
            models.Tag.owner_id == owner_id
        ).first()
        if tag:
            return tag
        raise HTTPException(status_code=409, detail="Tag creation conflict")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error creating tag '{tag_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to create tag")


def get_tags_by_user(db: Session, owner_id: int) -> list:
    """Get all tags for a user."""
    return db.query(models.Tag).filter(models.Tag.owner_id == owner_id).all()


def add_tag_to_note(db: Session, note_id: int, tag_name: str, owner_id: int) -> models.Tag:
    """Add a tag to a note (creates tag if doesn't exist)."""
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.owner_id == owner_id
    ).first()

    if not note:
        raise ValueError(f"Note {note_id} not found or not owned by user {owner_id}")

    tag = get_or_create_tag(db, tag_name, owner_id)

    # Add relationship if not exists
    if tag not in note.tags:
        note.tags.append(tag)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.exception(f"Error adding tag '{tag_name}' to note {note_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to add tag to note")

    return tag


def remove_tag_from_note(db: Session, note_id: int, tag_id: int, owner_id: int) -> bool:
    """Remove a tag from a note."""
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.owner_id == owner_id
    ).first()

    if not note:
        return False

    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()

    if tag and tag in note.tags:
        note.tags.remove(tag)
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Error removing tag {tag_id} from note {note_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove tag from note")

    return False


def add_tag_to_image(db: Session, image_id: int, tag_name: str, owner_id: int) -> models.Tag:
    """Add a tag to an image (creates tag if doesn't exist)."""
    image = db.query(models.Image).filter(
        models.Image.id == image_id,
        models.Image.owner_id == owner_id
    ).first()

    if not image:
        raise ValueError(f"Image {image_id} not found or not owned by user {owner_id}")

    tag = get_or_create_tag(db, tag_name, owner_id)

    # Add relationship if not exists
    if tag not in image.tags:
        image.tags.append(tag)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.exception(f"Error adding tag '{tag_name}' to image {image_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to add tag to image")

    return tag


def remove_tag_from_image(db: Session, image_id: int, tag_id: int, owner_id: int) -> bool:
    """Remove a tag from an image."""
    image = db.query(models.Image).filter(
        models.Image.id == image_id,
        models.Image.owner_id == owner_id
    ).first()

    if not image:
        return False

    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()

    if tag and tag in image.tags:
        image.tags.remove(tag)
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Error removing tag {tag_id} from image {image_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove tag from image")

    return False


def update_note(db: Session, note_id: int, title: Optional[str] = None, content: Optional[str] = None, owner_id: Optional[int] = None) -> Optional[models.Note]:
    """Update a note, regenerate slug if title changes, and extract tags."""
    from wikilink_parser import extract_hashtags
    from tasks_embeddings import generate_note_embedding_task

    note = db.query(models.Note).filter(models.Note.id == note_id).first()

    if not note:
        return None

    # Check ownership if owner_id provided
    if owner_id and note.owner_id != owner_id:
        return None

    # Track if content changed (for embedding regeneration)
    content_changed = False

    if title is not None:
        note.title = title

        # Generate unique slug for the new title
        base_slug = create_slug(title)
        slug = base_slug
        counter = 2

        # Check for existing slug (excluding current note)
        while db.query(models.Note).filter(
            models.Note.slug == slug,
            models.Note.owner_id == note.owner_id,
            models.Note.id != note_id
        ).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1

        note.slug = slug
        content_changed = True  # Title change affects embedding

    if content is not None:
        note.content = content
        content_changed = True

        # Extract and update tags from content
        hashtags = extract_hashtags(content)

        # Remove old tags that are no longer in content
        existing_tag_names = {tag.name for tag in note.tags}
        tags_to_remove = existing_tag_names - hashtags

        for tag_name in tags_to_remove:
            tag = next((t for t in note.tags if t.name == tag_name), None)
            if tag:
                note.tags.remove(tag)

        # Add new tags
        for tag_name in hashtags:
            if tag_name not in existing_tag_names:
                try:
                    tag = get_or_create_tag(db, tag_name, owner_id or note.owner_id)
                    note.tags.append(tag)
                except Exception as e:
                    logger.error(f"Error adding tag {tag_name} to note {note_id}: {e}", exc_info=True)

    try:
        db.commit()
        db.refresh(note)
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")

    # Trigger embedding regeneration if content changed (async, non-blocking)
    if content_changed:
        try:
            generate_note_embedding_task.delay(note_id)
        except Exception as e:
            logger.error(f"Failed to queue embedding generation for note {note_id}: {e}", exc_info=True)

    return note


def delete_note(db: Session, note_id: int, owner_id: Optional[int] = None) -> bool:
    """Delete a note. Returns True if successful, False if not found or not authorized."""
    note = db.query(models.Note).filter(models.Note.id == note_id).first()

    if not note:
        return False

    # Check ownership if owner_id provided
    if owner_id and note.owner_id != owner_id:
        return False

    db.delete(note)
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")
