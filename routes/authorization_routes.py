"""
The contents of this file are property of pygate.org
Review the Apache License 2.0 for valid authorization of use
See https://github.com/pypeople-dev/pygate for more information
"""

# External imports
from fastapi import APIRouter, Request, FastAPI, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
import logging

# Internal imports
from services.user_service import UserService
from utils.token import create_access_token
from utils.auth_util import auth_required
from utils.auth_blacklist import TimedHeap, jwt_blacklist

authorization_router = APIRouter()

"""
Login endpoint
Request:
{
    "email": "<string>",
    "password": "<string>"
}
Response:
{
    "access_token": "<string>",
    "token_type": "bearer"
}
"""
@authorization_router.post("/authorization")
async def login(request: Request, Authorize: AuthJWT = Depends()):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Missing email or password"
        )
    try:
        user = await UserService.check_password_return_user(email, password)
        access_token = create_access_token({"sub": user["email"], "role": user["role"]}, Authorize)
        response = JSONResponse(content={"message": "You are logged in"}, media_type="application/json")
        Authorize.set_access_cookies(access_token, response)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

"""
Status endpoint
Request:
{
}
Response:
{
}
"""
@authorization_router.get("/authorization/status")
@auth_required()
async def status(request: Request, Authorize: AuthJWT = Depends()):
    try:
        return JSONResponse(content={"status": "authorized"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
        
"""
Logout endpoint
Request:
{
}
Response:
{
    "message": "You are logged out"
}
"""
@authorization_router.post("/authorization/logout")
@auth_required()
async def logout(response: Response, Authorize: AuthJWT = Depends()):
    try:
        jwt_id = Authorize.get_raw_jwt()['jti']
        user = Authorize.get_jwt_subject()
        Authorize.unset_jwt_cookies(response)
        # Add JWT ID to blacklist
        if user not in jwt_blacklist:
            jwt_blacklist[user] = TimedHeap()
        jwt_blacklist[user].push(jwt_id)
        return JSONResponse(content={"message": "You are logged out"}, status_code=200)
    except AuthJWTException as e:
        logging.error(f"Logout failed: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": "An error occurred during logout"})
