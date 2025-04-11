from faker import Faker
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')
fake = Faker('uk_UA')  # Ukrainian locale for appropriate names/addresses

class BaseFactory:
    """Base factory for model generation"""
    model: Type[T] = None

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> T:
        """Create and persist a model instance"""
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj
        
    @classmethod
    def build(cls, **kwargs) -> T:
        """Build but don't persist a model instance"""
        if cls.model is None:
            raise NotImplementedError("Subclasses must define 'model'")
        return cls.model(**{**cls._get_defaults(), **kwargs})
    
    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for model fields"""
        return {}
        
    @classmethod
    async def create_batch(cls, session: AsyncSession, size: int, **kwargs) -> List[T]:
        """Create multiple instances with same base attributes"""
        return [await cls.create(session, **kwargs) for _ in range(size)]

    @classmethod
    def build_batch(cls, size: int, **kwargs) -> List[T]:
        """Build multiple instances with same base attributes"""
        return [cls.build(**kwargs) for _ in range(size)]
    
    @classmethod
    async def ensure_exists(cls, session, **kwargs):
        """Get entity if exists, or create if not"""
        model_class = cls.model
        
        # Build query dynamically based on kwargs
        query = select(model_class)
        for key, value in kwargs.items():
            if hasattr(model_class, key):
                query = query.where(getattr(model_class, key) == value)
        
        result = await session.execute(query)
        entity = result.scalars().first()
        
        if entity is None:
            entity = await cls.create(session, **kwargs)
            
        return entity