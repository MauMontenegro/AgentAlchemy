from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.services.db_connection import AsyncSessionLocal
from src.services.schemas_crud import (
    create_schema,
    get_schemas,
    get_schema_by_id,
    update_schema,
    delete_schema
)
from src.schemas.db_schemas import SchemaCreate, SchemaUpdate, SchemaOut
from src.dependencies import get_current_user
from src.models.models import User

# Dependency para obtener sesión DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

router = APIRouter()


# Crear esquema
@router.post("/", response_model=SchemaOut, status_code=status.HTTP_201_CREATED)
async def create_new_schema(
    schema: SchemaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_schema(db, user_id=current_user.id, schema_data=schema)

# Obtener todos los esquemas del usuario actual
@router.get("/", response_model=List[SchemaOut])
async def list_user_schemas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_schemas(db, user_id=current_user.id)

# Obtener un esquema específico
@router.get("/{schema_id}", response_model=SchemaOut)
async def get_single_schema(
    schema_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schema = await get_schema_by_id(db, schema_id, user_id=current_user.id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema

# Actualizar esquema
@router.put("/{schema_id}", response_model=SchemaOut)
async def update_user_schema(
    schema_id: int,
    schema_data: SchemaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await get_schema_by_id(db, schema_id, user_id=current_user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schema not found")

    return await update_schema(db, schema_id, schema_data)

# Eliminar esquema
@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_schema(
    schema_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schema = await get_schema_by_id(db, schema_id, user_id=current_user.id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    await delete_schema(db, schema_id)
    return None