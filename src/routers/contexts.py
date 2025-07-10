from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.services.db_connection import AsyncSessionLocal
from src.services.context_crud import (
    create_context,
    get_contexts,
    get_context_by_id,
    update_context,
    delete_context
)
from src.schemas.db_schemas import ContextCreate, ContextUpdate, ContextOut
from src.dependencies import get_current_user
from src.models.models import User

# Dependency para obtener sesión DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

router = APIRouter(prefix="/contexts", tags=["Contexts"])

# Crear contexto
@router.post("/", response_model=ContextOut, status_code=status.HTTP_201_CREATED)
async def create_new_context(
    context: ContextCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_context(db, user_id=current_user.id, context_data=context)

# Obtener todos los contextos del usuario actual
@router.get("/", response_model=List[ContextOut])
async def list_user_contexts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_contexts(db, user_id=current_user.id)

# Obtener un contexto específico
@router.get("/{context_id}", response_model=ContextOut)
async def get_single_context(
    context_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    context = await get_context_by_id(db, context_id, user_id=current_user.id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context

# Actualizar contexto
@router.put("/{context_id}", response_model=ContextOut)
async def update_user_context(
    context_id: int,
    context_data: ContextUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await get_context_by_id(db, context_id, user_id=current_user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Context not found")

    return await update_context(db, context_id, context_data)

# Eliminar contexto
@router.delete("/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_context(
    context_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    context = await get_context_by_id(db, context_id, user_id=current_user.id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    await delete_context(db, context_id)
    return None
