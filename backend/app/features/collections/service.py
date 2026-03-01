"""
Note Collections - Service Layer

Business logic for note collection operations.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import NoteCollection, NoteCollectionNote, NoteCollectionDocument, Note, Document

logger = logging.getLogger(__name__)


def get_collections(db: Session, owner_id: int) -> List[dict]:
    """Get all collections for a user with note counts."""
    collections = db.query(NoteCollection).filter(
        NoteCollection.owner_id == owner_id
    ).order_by(NoteCollection.name).all()

    result = []
    for collection in collections:
        note_count = db.query(func.count(NoteCollectionNote.note_id)).filter(
            NoteCollectionNote.collection_id == collection.id
        ).scalar()

        document_count = db.query(func.count(NoteCollectionDocument.document_id)).filter(
            NoteCollectionDocument.collection_id == collection.id
        ).scalar()

        result.append({
            "id": collection.id,
            "owner_id": collection.owner_id,
            "name": collection.name,
            "description": collection.description,
            "icon": collection.icon,
            "color": collection.color,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "note_count": note_count or 0,
            "document_count": document_count or 0
        })

    return result


def get_collection(db: Session, collection_id: int, owner_id: int) -> Optional[dict]:
    """Get a single collection with its notes."""
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return None

    # Get notes in this collection
    notes = db.query(Note).join(
        NoteCollectionNote,
        Note.id == NoteCollectionNote.note_id
    ).filter(
        NoteCollectionNote.collection_id == collection_id,
        Note.is_trashed == False
    ).order_by(NoteCollectionNote.position, Note.updated_at.desc()).all()

    # Get documents in this collection
    documents = db.query(Document).join(
        NoteCollectionDocument,
        Document.id == NoteCollectionDocument.document_id
    ).filter(
        NoteCollectionDocument.collection_id == collection_id,
        Document.is_trashed == False
    ).order_by(NoteCollectionDocument.position, Document.uploaded_at.desc()).all()

    return {
        "id": collection.id,
        "owner_id": collection.owner_id,
        "name": collection.name,
        "description": collection.description,
        "icon": collection.icon,
        "color": collection.color,
        "created_at": collection.created_at,
        "updated_at": collection.updated_at,
        "note_count": len(notes),
        "document_count": len(documents),
        "notes": [
            {
                "id": note.id,
                "title": note.title,
                "created_at": note.created_at
            }
            for note in notes
        ],
        "documents": [
            {
                "id": doc.id,
                "display_name": doc.display_name,
                "filename": doc.filename,
                "uploaded_at": doc.uploaded_at
            }
            for doc in documents
        ]
    }


def create_collection(
    db: Session,
    owner_id: int,
    name: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None
) -> NoteCollection:
    """Create a new note collection."""
    collection = NoteCollection(
        owner_id=owner_id,
        name=name,
        description=description,
        icon=icon,
        color=color
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)

    logger.info(f"Created collection '{name}' for user {owner_id}")
    return collection


def update_collection(
    db: Session,
    collection_id: int,
    owner_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[NoteCollection]:
    """Update a collection."""
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return None

    if name is not None:
        collection.name = name
    if description is not None:
        collection.description = description
    if icon is not None:
        collection.icon = icon
    if color is not None:
        collection.color = color

    db.commit()
    db.refresh(collection)

    logger.info(f"Updated collection {collection_id}")
    return collection


def delete_collection(db: Session, collection_id: int, owner_id: int) -> bool:
    """Delete a collection (notes are NOT deleted, just unlinked)."""
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    db.delete(collection)
    db.commit()

    logger.info(f"Deleted collection {collection_id}")
    return True


def add_note_to_collection(
    db: Session,
    collection_id: int,
    note_id: int,
    owner_id: int
) -> bool:
    """Add a note to a collection."""
    # Verify ownership
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        return False

    # Check if already in collection
    existing = db.query(NoteCollectionNote).filter(
        NoteCollectionNote.collection_id == collection_id,
        NoteCollectionNote.note_id == note_id
    ).first()

    if existing:
        return True  # Already in collection

    # Add to collection
    link = NoteCollectionNote(
        collection_id=collection_id,
        note_id=note_id
    )
    db.add(link)
    db.commit()

    logger.info(f"Added note {note_id} to collection {collection_id}")
    return True


def remove_note_from_collection(
    db: Session,
    collection_id: int,
    note_id: int,
    owner_id: int
) -> bool:
    """Remove a note from a collection."""
    # Verify ownership
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    # Remove link
    link = db.query(NoteCollectionNote).filter(
        NoteCollectionNote.collection_id == collection_id,
        NoteCollectionNote.note_id == note_id
    ).first()

    if not link:
        return False

    db.delete(link)
    db.commit()

    logger.info(f"Removed note {note_id} from collection {collection_id}")
    return True


def get_note_collections(db: Session, note_id: int, owner_id: int) -> List[dict]:
    """Get all collections that contain a specific note."""
    collections = db.query(NoteCollection).join(
        NoteCollectionNote,
        NoteCollection.id == NoteCollectionNote.collection_id
    ).filter(
        NoteCollectionNote.note_id == note_id,
        NoteCollection.owner_id == owner_id
    ).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "color": c.color
        }
        for c in collections
    ]


def add_document_to_collection(
    db: Session,
    collection_id: int,
    document_id: int,
    owner_id: int
) -> bool:
    """Add a document to a collection."""
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == owner_id
    ).first()

    if not doc:
        return False

    existing = db.query(NoteCollectionDocument).filter(
        NoteCollectionDocument.collection_id == collection_id,
        NoteCollectionDocument.document_id == document_id
    ).first()

    if existing:
        return True

    link = NoteCollectionDocument(
        collection_id=collection_id,
        document_id=document_id
    )
    db.add(link)
    db.commit()

    logger.info(f"Added document {document_id} to collection {collection_id}")
    return True


def remove_document_from_collection(
    db: Session,
    collection_id: int,
    document_id: int,
    owner_id: int
) -> bool:
    """Remove a document from a collection."""
    collection = db.query(NoteCollection).filter(
        NoteCollection.id == collection_id,
        NoteCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    link = db.query(NoteCollectionDocument).filter(
        NoteCollectionDocument.collection_id == collection_id,
        NoteCollectionDocument.document_id == document_id
    ).first()

    if not link:
        return False

    db.delete(link)
    db.commit()

    logger.info(f"Removed document {document_id} from collection {collection_id}")
    return True


def get_document_collections(db: Session, document_id: int, owner_id: int) -> List[dict]:
    """Get all collections that contain a specific document."""
    collections = db.query(NoteCollection).join(
        NoteCollectionDocument,
        NoteCollection.id == NoteCollectionDocument.collection_id
    ).filter(
        NoteCollectionDocument.document_id == document_id,
        NoteCollection.owner_id == owner_id
    ).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "color": c.color
        }
        for c in collections
    ]
