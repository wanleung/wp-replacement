from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import WPUser
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: WPUser = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(get_current_user),
):
    if data.user_email is not None:
        current_user.user_email = data.user_email
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.user_url is not None:
        current_user.user_url = data.user_url
    if data.password is not None:
        current_user.user_pass = hash_password(data.password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_admin),
):
    return db.query(WPUser).order_by(WPUser.user_registered.desc()).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: WPUser = Depends(require_admin),
):
    if db.query(WPUser).filter(WPUser.user_login == data.user_login).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(WPUser).filter(WPUser.user_email == data.user_email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = WPUser(
        user_login=data.user_login,
        user_pass=hash_password(data.password),
        user_email=data.user_email,
        user_nicename=data.user_nicename or data.user_login,
        display_name=data.display_name or data.user_login,
        user_url=data.user_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
