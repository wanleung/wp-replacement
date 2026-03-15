from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import WPUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> WPUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    user = db.query(WPUser).filter(WPUser.ID == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def require_editor(current_user: WPUser = Depends(get_current_user)) -> WPUser:
    """Allow only users with editor or administrator capability."""
    caps = current_user.capabilities
    if not (caps.get("administrator") or caps.get("editor")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_admin(current_user: WPUser = Depends(get_current_user)) -> WPUser:
    caps = current_user.capabilities
    if not caps.get("administrator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )
    return current_user
