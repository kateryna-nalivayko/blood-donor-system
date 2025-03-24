from app.dao.base import BaseDAO
from app.users.models import User
from app.database import async_session_maker
from typing import Optional
from sqlalchemy import select


class UsersDAO(BaseDAO):
    model = User


    @classmethod
    async def set_single_role(cls, user_id: int, role_name: str) -> Optional[User]:
        """
        Set a single role for a user, making it the only active role.
        The 'user' role remains always active.
        
        Args:
            user_id: ID of the user to update
            role_name: Name of the role to set (admin, super_admin, donor, hospital_staff)
            
        Returns:
            Updated User object or None if user not found
        """
        valid_roles = ["admin", "super_admin", "donor", "hospital_staff"]
        if role_name not in valid_roles:
            raise ValueError(f"Invalid role: {role_name}. Must be one of {valid_roles}")

        async with async_session_maker() as session:
            async with session.begin():
                # Find the user
                user = await session.execute(select(cls.model).filter_by(id=user_id))
                user = user.scalar_one_or_none()
                
                if not user:
                    return None
                
                user.is_admin = False
                user.is_super_admin = False
                user.is_donor = False
                user.is_hospital_staff = False
                
                if role_name == "admin":
                    user.is_admin = True
                elif role_name == "super_admin":
                    user.is_super_admin = True
                elif role_name == "donor":
                    user.is_donor = True
                elif role_name == "hospital_staff":
                    user.is_hospital_staff = True
                

                session.add(user)
                await session.refresh(user)
                await session.commit()
                
                return user