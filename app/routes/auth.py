import os

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": (
            "openid email profile "
            "https://www.googleapis.com/auth/gmail.readonly"
        )
    },
)


@router.get("/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    if not user_info:
        return JSONResponse(
            status_code=400,
            content={"detail": "Google user information not found"},
        )

    email = user_info.get("email")

    if not email:
        return JSONResponse(
            status_code=400,
            content={"detail": "Google account email not found"},
        )

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            email=email,
            name=user_info.get("name"),
            google_id=user_info.get("sub"),
            picture=user_info.get("picture"),
            access_token=token.get("access_token"),
            refresh_token=token.get("refresh_token"),
            token_expiry=str(token.get("expires_at"))
            if token.get("expires_at")
            else None,
        )

        db.add(user)

    else:
        user.name = user_info.get("name")
        user.google_id = user_info.get("sub")
        user.picture = user_info.get("picture")

        if token.get("access_token"):
            user.access_token = token.get("access_token")

        if token.get("refresh_token"):
            user.refresh_token = token.get("refresh_token")

        if token.get("expires_at"):
            user.token_expiry = str(token.get("expires_at"))

    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    return RedirectResponse(
        url=frontend_url,
        status_code=302,
    )


@router.get("/me")
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Logged out successfully"
    }