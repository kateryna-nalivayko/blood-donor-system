import bcrypt
from sqlalchemy import select
from app.users.models import User
from .base_factory import BaseFactory, fake

class UserFactory(BaseFactory):
    model = User
    
    @classmethod
    def _get_defaults(cls):
        """Generate default user data"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        

        password = "Password123!"
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')

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
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}",
            "phone_number": f"+380{fake.numerify('#########')}",
            "password": hashed_password,
            "is_user": True,
            "is_admin": False,
            "is_super_admin": False,
            "is_donor": False,
            "is_hospital_staff": False
        }
    