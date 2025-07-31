from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.models import Esquema
from src.schemas.db_schemas import SchemaCreate, SchemaUpdate

# Create a new schema for a given user
async def create_schema(db: AsyncSession, user_id: int, schema_data: SchemaCreate):
    try:
        db_schema = Esquema(
            name=schema_data.name,
            description=schema_data.description,
            schema_data=schema_data.schema_data,
            user_id=user_id
        )
        db.add(db_schema)
        await db.commit()
        await db.refresh(db_schema)
        return db_schema
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create schema: {str(e)}") from e

# Get all schemas (optionally filtered by user)
async def get_schemas(db: AsyncSession, user_id: int = None):
    stmt = select(Esquema)
    if user_id:
        stmt = stmt.where(Esquema.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# Get a specific schema by ID (and optional user validation)
async def get_schema_by_id(db: AsyncSession, schema_id: int, user_id: int = None):
    stmt = select(Esquema).where(Esquema.id == schema_id)
    if user_id:
        stmt = stmt.where(Esquema.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Update a schema
async def update_schema(db: AsyncSession, schema_id: int, schema_data: SchemaUpdate):
    result = await db.execute(select(Esquema).where(Esquema.id == schema_id))
    schema = result.scalar_one_or_none()

    if not schema:
        return None

    if schema_data.name is not None:
        schema.name = schema_data.name
    if schema_data.description is not None:
        schema.description = schema_data.description
    if schema_data.schema_data is not None:
        schema.schema_data = schema_data.schema_data

    await db.commit()
    await db.refresh(schema)
    return schema

# Delete a schema
async def delete_schema(db: AsyncSession, schema_id: int):
    result = await db.execute(select(Esquema).where(Esquema.id == schema_id))
    schema = result.scalar_one_or_none()
    if schema:
        await db.delete(schema)
        await db.commit()
        return True
    return False