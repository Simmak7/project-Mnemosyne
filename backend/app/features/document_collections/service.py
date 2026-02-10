"""
Document Collections - Service Layer

Business logic for document collection operations.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import DocumentCollection, DocumentCollectionDocument, Document

logger = logging.getLogger(__name__)


def get_collections(db: Session, owner_id: int) -> List[dict]:
    """Get all collections for a user with document counts."""
    collections = db.query(DocumentCollection).filter(
        DocumentCollection.owner_id == owner_id
    ).order_by(DocumentCollection.name).all()

    result = []
    for collection in collections:
        doc_count = db.query(func.count(DocumentCollectionDocument.document_id)).filter(
            DocumentCollectionDocument.collection_id == collection.id
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
            "document_count": doc_count or 0
        })

    return result


def get_collection(db: Session, collection_id: int, owner_id: int) -> Optional[dict]:
    """Get a single collection with its documents."""
    collection = db.query(DocumentCollection).filter(
        DocumentCollection.id == collection_id,
        DocumentCollection.owner_id == owner_id
    ).first()

    if not collection:
        return None

    documents = db.query(Document).join(
        DocumentCollectionDocument,
        Document.id == DocumentCollectionDocument.document_id
    ).filter(
        DocumentCollectionDocument.collection_id == collection_id,
        Document.is_trashed == False
    ).order_by(DocumentCollectionDocument.position, Document.uploaded_at.desc()).all()

    return {
        "id": collection.id,
        "owner_id": collection.owner_id,
        "name": collection.name,
        "description": collection.description,
        "icon": collection.icon,
        "color": collection.color,
        "created_at": collection.created_at,
        "updated_at": collection.updated_at,
        "document_count": len(documents),
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
) -> DocumentCollection:
    """Create a new document collection."""
    collection = DocumentCollection(
        owner_id=owner_id,
        name=name,
        description=description,
        icon=icon,
        color=color
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    logger.info(f"Created document collection '{name}' for user {owner_id}")
    return collection


def update_collection(
    db: Session,
    collection_id: int,
    owner_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[DocumentCollection]:
    """Update a document collection."""
    collection = db.query(DocumentCollection).filter(
        DocumentCollection.id == collection_id,
        DocumentCollection.owner_id == owner_id
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
    logger.info(f"Updated document collection {collection_id}")
    return collection


def delete_collection(db: Session, collection_id: int, owner_id: int) -> bool:
    """Delete a collection (documents are NOT deleted, just unlinked)."""
    collection = db.query(DocumentCollection).filter(
        DocumentCollection.id == collection_id,
        DocumentCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    db.delete(collection)
    db.commit()
    logger.info(f"Deleted document collection {collection_id}")
    return True


def add_document_to_collection(
    db: Session,
    collection_id: int,
    document_id: int,
    owner_id: int
) -> bool:
    """Add a document to a collection."""
    collection = db.query(DocumentCollection).filter(
        DocumentCollection.id == collection_id,
        DocumentCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == owner_id
    ).first()

    if not doc:
        return False

    existing = db.query(DocumentCollectionDocument).filter(
        DocumentCollectionDocument.collection_id == collection_id,
        DocumentCollectionDocument.document_id == document_id
    ).first()

    if existing:
        return True

    link = DocumentCollectionDocument(
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
    collection = db.query(DocumentCollection).filter(
        DocumentCollection.id == collection_id,
        DocumentCollection.owner_id == owner_id
    ).first()

    if not collection:
        return False

    link = db.query(DocumentCollectionDocument).filter(
        DocumentCollectionDocument.collection_id == collection_id,
        DocumentCollectionDocument.document_id == document_id
    ).first()

    if not link:
        return False

    db.delete(link)
    db.commit()
    logger.info(f"Removed document {document_id} from collection {collection_id}")
    return True


def get_document_collections(db: Session, document_id: int, owner_id: int) -> List[dict]:
    """Get all collections that contain a specific document."""
    collections = db.query(DocumentCollection).join(
        DocumentCollectionDocument,
        DocumentCollection.id == DocumentCollectionDocument.collection_id
    ).filter(
        DocumentCollectionDocument.document_id == document_id,
        DocumentCollection.owner_id == owner_id
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
