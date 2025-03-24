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
            **values: Именованные параметры для создания нового экземпляра модели.

        Returns:
            The created instance of the model.
        """
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance
            

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