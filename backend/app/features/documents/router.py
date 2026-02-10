"""
Documents Feature - Router Combiner

Imports and combines all document sub-routers.
"""

from fastapi import APIRouter

from features.documents.router_upload import router as upload_router
from features.documents.router_crud import router as crud_router
from features.documents.router_review import router as review_router

router = APIRouter(tags=["Documents"])
router.include_router(upload_router)
router.include_router(crud_router)
router.include_router(review_router)
