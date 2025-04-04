from app.dao.base import BaseDAO
from app.users.models import User
from app.database import async_session_maker
from typing import Optional
from sqlalchemy import func, or_, select
from app.donor.dao import DonorDAO
from app.hospital_staff.dao import HospitalStaffDAO

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
                
            return user
        


    @classmethod
    async def find_paginated(cls, page: int = 1, limit: int = 10):
        """Find users with pagination"""
        offset = (page - 1) * limit
        
        async with async_session_maker() as session:
            # Get total count
            total_count_query = select(func.count(User.id))
            total_count = await session.scalar(total_count_query)
            
            # Get users for the page
            query = select(User).order_by(User.id).offset(offset).limit(limit)
            result = await session.execute(query)
            users = result.scalars().all()
            
            return users, total_count

    @classmethod
    async def search_paginated(cls, search_term: str, page: int = 1, limit: int = 10):
        """Search users with pagination"""
        offset = (page - 1) * limit
        search_pattern = f"%{search_term}%"
        
        async with async_session_maker() as session:
            # Get total count of matching users
            total_count_query = select(func.count(User.id)).where(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.phone_number.ilike(search_pattern)
                )
            )
            total_count = await session.scalar(total_count_query)
            
            # Get matching users for the page
            query = select(User).where(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.phone_number.ilike(search_pattern)
                )
            ).order_by(User.id).offset(offset).limit(limit)
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            return users, total_count

    @classmethod
    async def find_recent(cls, limit: int = 5):
        """Find most recently registered users"""
        async with async_session_maker() as session:
            query = select(User).order_by(User.created_at.desc()).limit(limit)
            result = await session.execute(query)
            users = result.scalars().all()
            
            return users

    @classmethod
    async def count(cls):
        """Get total count of users"""
        async with async_session_maker() as session:
            query = select(func.count(User.id))
            result = await session.scalar(query)
            
            return result


    @classmethod
    async def update(cls, id: int, **kwargs):
        """
        Update a user by ID with the provided keyword arguments.
        
        Args:
            id: The ID of the user to update
            **kwargs: The attributes to update
            
        Returns:
            The updated user object
        """
        async with async_session_maker() as session:
            async with session.begin():

                query = select(cls.model).filter_by(id=id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                

                for key, value in kwargs.items():
                    setattr(user, key, value)
                
                session.add(user)
                

            await session.refresh(user)
            return user