from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.core.security import create_access_token, hash_password, verify_password
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id, name=user.name, email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        classroom_id=user.classroom_id, created_at=user.created_at,
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        # Public sign-up never grants privileged roles. Admins may be seeded or
        # created through an authenticated administration flow.
        role=UserRole.EMPLOYEE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.email)
    
    return TokenResponse(access_token=token, user=to_user_response(user))

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        login_value = (payload.email or payload.username or "").strip().lower()
        if not login_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username or email is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if "@" in login_value:
            user = db.query(User).filter(User.email == login_value).first()
        else:
            user = db.query(User).filter(
                or_(
                    User.email == login_value,
                    User.email == f"{login_value}@test.com",
                    func.lower(User.name) == login_value,
                )
            ).first()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(subject=user.email)

        return TokenResponse(access_token=token, user=to_user_response(user))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_info = traceback.format_exc()
        print(f"LOGIN ERROR: {e}\n{error_info}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during login: {str(e)}\n{error_info}")

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return to_user_response(current_user)


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Directory for authorized administration and task-assignment UIs."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User directory access is restricted")
    return [to_user_response(user) for user in db.query(User).order_by(User.name.asc()).all()]
