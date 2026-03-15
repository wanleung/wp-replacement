from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import WPUser
from app.core.security import verify_password, create_access_token
from app.schemas.user import TokenResponse, LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(db: Session, username: str, password: str) -> WPUser | None:
    user = (
        db.query(WPUser)
        .filter(
            (WPUser.user_login == username) | (WPUser.user_email == username)
        )
        .first()
    )
    if not user:
        return None
    if not verify_password(password, user.user_pass):
        return None
    return user


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password flow — accepts username/email + password."""
    user = _authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.ID)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    """JSON login endpoint for frontend convenience."""
    user = _authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(subject=user.ID)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
