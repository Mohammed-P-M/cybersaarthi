from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.database import User
from app.schemas.pydantic_models import UserAuth, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(user_data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        # Default investigator account auto-creation for out-of-the-box convenience
        if user_data.username in ["investigator", "admin"] and user_data.password in ["investigator123", "admin123"]:
            user = User(
                username=user_data.username,
                email=f"{user_data.username}@cybersaarthi.gov.in",
                hashed_password=get_password_hash(user_data.password),
                role="INVESTIGATOR"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(status_code=400, detail="Invalid username or password")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token(subject=user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }
