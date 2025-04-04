from app.database import async_session_maker
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError


class BaseDAO:
    model = None


    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()


    @classmethod
    async def add(cls, **values):
        """
        Asynchronously creates a new instance of the model with the specified values.
        
        Arguments:
            **values: Named parameters for creating a new instance of the model.
            
        Returns:
            The created instance of the model.
        """
        async with async_session_maker() as session:
            # Remove ID if it's being passed manually
            if 'id' in values:
                del values['id']
                
            new_instance = cls.model(**values)
            session.add(new_instance)
            
            try:
                # Commit the session to save the new instance
                await session.commit()
                
                # Create a new transaction for the refresh operation
                # This is outside the previous transaction context
                await session.refresh(new_instance)
                return new_instance
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    @classmethod
    async def count(cls):
        """
        Count total number of records
        """
        async with async_session_maker() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(cls.model)
            result = await session.execute(query)
            return result.scalar() or 0


    @classmethod
    async def delete(cls, id: int) -> bool:
        """Delete a record by ID"""
        async with async_session_maker() as session:
            obj = await session.get(cls.model, id)
            if not obj:
                return False
            
            await session.delete(obj)
            await session.commit()
            return True
            

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        """
        Asynchronously finds and returns one instance of the model by the specified criteria or None.

        Arguments:
            data_id: The filtering criteria in the form of a record identifier.

        Returns:
            An instance of the model or None if nothing is found.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        

    @classmethod
    async def find_all(cls, **filter_by):
        """
        Asynchronously finds and returns all instances of the model that match the specified criteria.

        Arguments:
            **filter_by: Filtering criteria in the form of named parameters.

        Returns:
            A list of model instances.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()