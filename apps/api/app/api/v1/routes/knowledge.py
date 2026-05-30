from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.security import CurrentUser, get_current_user
from app.db.repositories.knowledge import KnowledgeRepository
from app.schemas.knowledge import (
    CollectionCreate,
    CollectionRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.rag.service import RAGService

router = APIRouter()


@router.get("/collections", response_model=list[CollectionRead])
async def list_collections(
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[CollectionRead]:
    repository = KnowledgeRepository(session)
    collections = await repository.list_collections(user.id)
    return [CollectionRead.model_validate(collection) for collection in collections]


@router.post("/collections", response_model=CollectionRead, status_code=201)
async def create_collection(
    payload: CollectionCreate,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> CollectionRead:
    repository = KnowledgeRepository(session)
    collection = await repository.create_collection(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
    )
    await session.commit()
    return CollectionRead.model_validate(collection)


@router.post("/collections/{collection_id}/upload")
async def upload_document(
    collection_id: str,
    file: UploadFile = File(...),
    tags: str = Form(default=""),
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    tag_values = [tag.strip() for tag in tags.split(",") if tag.strip()]
    try:
        result = await RAGService(session).ingest_upload(collection_id, user.id, file, tag_values)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()
    return result


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    session: AsyncSession = Depends(db_session),
) -> KnowledgeSearchResponse:
    results = await RAGService(session).search(
        query=payload.query,
        collection_ids=payload.collection_ids,
        tags=payload.tags,
        limit=payload.limit,
    )
    return KnowledgeSearchResponse(results=results)
