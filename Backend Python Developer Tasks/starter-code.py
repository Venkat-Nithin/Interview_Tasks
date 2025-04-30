# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.db.init_db import create_first_superuser

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    # This can cause startup delays
    create_first_superuser()


# app/api/endpoints/users.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    # Inefficient query with no filtering
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    # Directly manipulating user data without a service layer
    user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_superuser=user_in.is_superuser,
    )
    db.add(user)
    db.commit()
    
    # Missing db.refresh()
    
    return user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    full_name: str = None,
    email: str = None,
    password: str = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    # No transaction handling for updates
    if email:
        current_user.email = email
    if full_name:
        current_user.full_name = full_name
    if password:
        current_user.hashed_password = get_password_hash(password)
    
    db.add(current_user)
    db.commit()
    
    return current_user

@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # Security issue: any user can view any other user
    return user


# app/api/endpoints/content.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.worker import process_content_task

router = APIRouter()

@router.get("/", response_model=List[schemas.Content])
def read_content(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve content.
    """
    # N+1 query problem - fetching each owner separately
    content = db.query(models.Content).offset(skip).limit(limit).all()
    
    # Add owner information manually instead of using joins
    for item in content:
        item.owner = db.query(models.User).filter(models.User.id == item.owner_id).first()
    
    return content

@router.post("/", response_model=schemas.Content)
def create_content(
    *,
    db: Session = Depends(deps.get_db),
    content_in: schemas.ContentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new content.
    """
    # Not validating category exists
    content = models.Content(
        title=content_in.title,
        description=content_in.description,
        category_id=content_in.category_id,
        owner_id=current_user.id
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    
    # This will block the request
    process_content_task(content.id)
    
    return content

@router.put("/{id}", response_model=schemas.Content)
def update_content(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    content_in: schemas.ContentUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update content.
    """
    content = db.query(models.Content).filter(models.Content.id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Not checking if user owns the content
    if content_in.title is not None:
        content.title = content_in.title
    if content_in.description is not None:
        content.description = content_in.description
    if content_in.category_id is not None:
        # Not validating if category exists
        content.category_id = content_in.category_id
    
    db.add(content)
    db.commit()
    db.refresh(content)
    return content

@router.get("/{id}", response_model=schemas.Content)
def read_content_by_id(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get content by id.
    """
    content = db.query(models.Content).filter(models.Content.id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # No access control based on content visibility
    return content

@router.delete("/{id}", response_model=schemas.Content)
def delete_content(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete content.
    """
    content = db.query(models.Content).filter(models.Content.id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Not checking if user owns the content or has delete permission
    db.delete(content)
    db.commit()
    return content


# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Missing index on frequently queried fields
    
    # Relationships
    content = relationship("Content", back_populates="owner")
    
    # No cascading deletes defined


# app/models/content.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Content(Base):
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    
    # Missing created_at and updated_at timestamps
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("user.id"))
    category_id = Column(Integer, ForeignKey("category.id"))
    
    # Relationships
    owner = relationship("User", back_populates="content")
    category = relationship("Category", back_populates="content_items")
    
    # No cascading options defined

class Category(Base):
    __tablename__ = "category"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    
    # Relationships
    content_items = relationship("Content", back_populates="category")
    
    # No parent/child category relationship (hierarchical categories)


# app/core/auth.py
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    # Missing additional claims like token type, issued at, etc.
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    db: Session = Depends(SessionLocal),  # Incorrect dependency, should use deps.get_db
    token: str = Depends(oauth2_scheme),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenPayload(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # N+1 query problem - always fetching user
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user


# app/core/security.py
from datetime import datetime, timedelta
from typing import Any, Union

from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate(db: Session, *, email: str, password: str) -> Union[models.User, None]:
    # Inefficient - doing two separate queries
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    
    # Then checking if user is active
    if not user.is_active:
        return None
    
    # Finally checking password
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# app/worker.py
from celery import Celery
import time
from app.core.config import settings
from app.db.session import SessionLocal

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL)

@celery_app.task(name="process_content")
def process_content_task(content_id: int):
    """
    Process content in background.
    """
    # Creates new database session for each task - inefficient
    db = SessionLocal()
    
    try:
        # No error handling for missing content
        from app.models.content import Content
        content = db.query(Content).filter(Content.id == content_id).first()
        
        # Simulate processing - no error handling
        time.sleep(10)  # Blocking sleep - inefficient
        
        # Updates directly without checking if content exists
        content.title = f"Processed: {content.title}"
        db.add(content)
        db.commit()
    finally:
        db.close()

@celery_app.task(name="send_notifications")
def send_notifications():
    """
    Send periodic notifications about new content.
    """
    # Creates new database session
    db = SessionLocal()
    
    try:
        from app.models.content import Content
        from app.models.user import User
        
        # Inefficient query fetching all content and users
        all_content = db.query(Content).all()
        all_users = db.query(User).all()
        
        # Nested loops - very inefficient for large datasets
        for user in all_users:
            for content in all_content:
                # Simulating notification
                print(f"Notifying user {user.id} about content {content.id}")
    finally:
        db.close()


# app/api/deps.py
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
        
    # Always fetching user - inefficient for frequent requests
    user = db.query(models.User).filter(models.User.id == token_data.sub).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


# app/schemas/user.py
from typing import Optional

from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# app/schemas/content.py
from typing import Optional

from pydantic import BaseModel

# Shared properties
class ContentBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None

# Properties to receive on content creation
class ContentCreate(ContentBase):
    title: str
    category_id: int

# Properties to receive on content update
class ContentUpdate(ContentBase):
    pass

# Properties shared by models stored in DB
class ContentInDBBase(ContentBase):
    id: int
    title: str
    owner_id: int

    class Config:
        orm_mode = True

# Properties to return to client
class Content(ContentInDBBase):
    pass

# Properties stored in DB
class ContentInDB(ContentInDBBase):
    pass


# app/core/config.py
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ALGORITHM: str = "HS256"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "CMS API"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cmsdb"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    
    # No rate limiting configuration
    
    class Config:
        case_sensitive = True

settings = Settings()


# app/db/init_db.py
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db.session import SessionLocal

def create_first_superuser():
    db = SessionLocal()
    try:
        user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
        if not user:
            user_in = schemas.UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
            )
            user = crud.user.create(db, obj_in=user_in)
    finally:
        db.close()
