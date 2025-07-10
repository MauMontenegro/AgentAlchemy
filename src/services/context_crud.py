from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.models import Context
from src.schemas.db_schemas import ContextCreate, ContextUpdate
from sqlalchemy.exc import NoResultFound

# Create a new context for a given user
async def create_context(db: AsyncSession, user_id: int, context_data: ContextCreate):
    try:
        db_context = Context(
            name=context_data.name,
            description=context_data.description,
            user_id=user_id
        )
        db.add(db_context)
        await db.commit()
        await db.refresh(db_context)
        return db_context
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create context: {str(e)}") from e

# Get all contexts (optionally filtered by user)
async def get_contexts(db: AsyncSession, user_id: int = None):
    stmt = select(Context)
    if user_id:
        stmt = stmt.where(Context.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# Get a specific context by ID (and optional user validation)
async def get_context_by_id(db: AsyncSession, context_id: int, user_id: int = None):
    stmt = select(Context).where(Context.id == context_id)
    if user_id:
        stmt = stmt.where(Context.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Update a context
async def update_context(db: AsyncSession, context_id: int, context_data: ContextUpdate):
    result = await db.execute(select(Context).where(Context.id == context_id))
    context = result.scalar_one_or_none()

    if not context:
        return None

    if context_data.name is not None:
        context.name = context_data.name
    if context_data.description is not None:
        context.description = context_data.description

    await db.commit()
    await db.refresh(context)
    return context

# Delete a context
async def delete_context(db: AsyncSession, context_id: int):
    result = await db.execute(select(Context).where(Context.id == context_id))
    context = result.scalar_one_or_none()
    if context:
        await db.delete(context)
        await db.commit()
        return True
    return False
