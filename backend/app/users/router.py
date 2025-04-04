from fastapi import APIRouter, Body, HTTPException, Response, status, Depends

from app.users.dependencies import get_current_user, get_current_admin_user
from app.users.schemas import PasswordChange, RoleResponse, RoleUpdate, UserRegister, UserAuth
from app.users.dao import UsersDAO
from app.users.security import get_password_hash
from app.users.auth import authenticate_user, create_access_token
from app.users.models import User

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post("/register")
async def register_user(user_data: UserRegister) -> dict:
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='User already exists')
    user_dict = user_data.model_dump()
    user_dict['password'] = get_password_hash(user_data.password)
    await UsersDAO.add(**user_dict)
    return {'message': f'You are successfully registered!'}


@router.post("/login")
async def auth_user(response: Response, user_data: UserAuth):
    check = await authenticate_user(email=user_data.email,
                                    password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Incorrect email or password')
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="user_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 
            "refresh_token": None, 
            "message": f"User {check.email} successfully logged in"}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.post("/logout/", summary="Log out a user by deleting their access token cookie.")
async def logout_user(response: Response):
    response.delete_cookie(key="user_access_token")
    return {'message': 'User successfully logged out!'}


@router.get("/all_users")
async def get_all_users(user_data: User = Depends(get_current_admin_user)):
    return await UsersDAO.find_all()


@router.put("/users/{user_id}/role", 
           response_model=RoleResponse,
           status_code=status.HTTP_200_OK,
           summary="Set a single role for a user",
           description="Sets a single exclusive role for a user, removing all other roles except the basic user role.",
           dependencies=[Depends(get_current_admin_user)])
async def set_user_role(user_id: int, role_data: RoleUpdate):
    """
    Set a single exclusive role for a user.
    
    The user will have ONLY the specified role plus the basic user role.
    All other roles will be removed.
    
    Args:
        user_id: The ID of the user to update
        role_data: The role to set as the exclusive role
    """
    if role_data.role == "user":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                           detail="Cannot set USER as a single role - it's always enabled")
    
    updated_user = await UsersDAO.set_single_role(user_id, role_data.role)
    
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                           detail=f"User with ID {user_id} not found")
    
    return {"message": f"User with ID {user_id} now has the exclusive role: {role_data.role}"}



from fastapi import Path
from app.users.schemas import UserUpdate, UserResponse

@router.put("/users/{user_id}", 
           response_model=UserResponse,
           status_code=status.HTTP_200_OK,
           summary="Update user details",
           dependencies=[Depends(get_current_admin_user)])
async def update_user(
    user_id: int = Path(..., title="The ID of the user to update"),
    user_data: UserUpdate = Body(..., title="Updated user information")
):
    """
    Update a user's details.
    
    Args:
        user_id: The ID of the user to update
        user_data: The updated user information
        
    Returns:
        The updated user
    """
    user = await UsersDAO.find_one_or_none(id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if email is already taken by another user
    if user_data.email != user.email:
        existing_user = await UsersDAO.find_one_or_none(email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already taken by another user"
            )
    
    # Check if phone number is already taken by another user
    if user_data.phone_number != user.phone_number:
        existing_user = await UsersDAO.find_one_or_none(phone_number=user_data.phone_number)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already taken by another user"
            )
    
    # Update user
    updated_user = await UsersDAO.update(user_id, **user_data.model_dump())
    
    return updated_user


@router.delete("/users/{user_id}",
              status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete a user",
              dependencies=[Depends(get_current_admin_user)])
async def delete_user(user_id: int = Path(..., title="The ID of the user to delete")):
    """
    Delete a user.
    
    Args:
        user_id: The ID of the user to delete
        
    Returns:
        204 No Content response
    """
    user = await UsersDAO.find_one_or_none(id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if user is super admin
    if user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete a super admin user"
        )
    
    # Delete user
    await UsersDAO.delete(user_id)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/profile/update", 
          response_model=UserResponse,
          status_code=status.HTTP_200_OK,
          summary="Update current user's profile")
async def update_profile(
    user_data: UserUpdate = Body(..., title="Updated user information"),
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's profile details.
    
    Args:
        user_data: The updated user information
        
    Returns:
        The updated user
    """
    user_id = current_user.id
    
    # Check if email is already taken by another user
    if user_data.email != current_user.email:
        existing_user = await UsersDAO.find_one_or_none(email=user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already taken by another user"
            )
    
    # Check if phone number is already taken by another user
    if user_data.phone_number != current_user.phone_number:
        existing_user = await UsersDAO.find_one_or_none(phone_number=user_data.phone_number)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already taken by another user"
            )
    
    # Update user
    updated_user = await UsersDAO.update(user_id, **user_data.model_dump())
    
    return updated_user


@router.post("/profile/change-password", 
          status_code=status.HTTP_200_OK,
          summary="Change current user's password")
async def change_password(
    password_data: PasswordChange = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Change the current user's password.
    
    Args:
        password_data: Current password and new password
        
    Returns:
        Success message
    """
    # Verify current password
    user = await UsersDAO.find_one_or_none(id=current_user.id)
    
    from app.users.security import verify_password
    if not verify_password(password_data.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Check if new passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    # Update password
    from app.users.security import get_password_hash
    hashed_password = get_password_hash(password_data.new_password)
    await UsersDAO.update(current_user.id, password=hashed_password)
    
    return {"message": "Password changed successfully"}