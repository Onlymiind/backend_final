import jose
from jose import jwt
from typing import Any

from datetime import timedelta, datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy import select

from app.models import models
from app.schemas import schemas
from app.core import database
from app.core import config


_PWD_CONTEXT = CryptContext(
    schemes=["bcrypt_sha256"],
    bcrypt__truncate_error=False,
    deprecated="auto",
)


def get_password_hash(password: str):
    return _PWD_CONTEXT.hash(password)


class Service:
    def __init__(
        self,
        db: AsyncSession,
        secret_key: str,
        algorithm: str,
        token_duration: timedelta,
    ) -> None:
        self.db = db
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_duration = token_duration

    async def register(self, request: schemas.RegisterRequest) -> None:
        result = await self.db.execute(
            select(models.User).where(models.User.login == request.login)
        )
        if result.scalars().first():
            raise HTTPException(status_code=409, detail="User already exists")

        if len(request.password) > 72:
            raise HTTPException(status_code=400, detail="Password too long")

        user = models.User(
            login=request.login,
            password_hash=_PWD_CONTEXT.hash(request.password),
        )
        self.db.add(user)
        await self.db.commit()

    async def authorize(self, login: str, password: str) -> schemas.AuthorizeResponse:
        result = await self.db.execute(
            select(models.User).where(models.User.login == login)
        )
        user = result.scalars().one_or_none()
        if not user or not _PWD_CONTEXT.verify(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return schemas.AuthorizeResponse(
            access_token=self._create_access_token(user.id),
            token_type="bearer",
        )

    async def refresh(self, user: models.User) -> schemas.AuthorizeResponse:
        return schemas.AuthorizeResponse(
            access_token=self._create_access_token(user.id),
            token_type="bearer",
        )

    async def change_password(
        self, request: schemas.ChangePasswordRequest, user: models.User
    ) -> None:
        if not _PWD_CONTEXT.verify(request.old_password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user.password_hash = _PWD_CONTEXT.hash(request.new_password)
        await self.db.commit()

    def _create_access_token(self, subject: int) -> str:
        expire = datetime.now(timezone.utc) + self.token_duration
        payload: dict[str, Any] = {
            "exp": expire.timestamp(),
            "sub": str(subject),
            "type": "access",
        }
        return jwt.encode(claims=payload, key=self.secret_key, algorithm=self.algorithm)


def get_service(
    db: AsyncSession = Depends(database.get_db),
    config: config.Config = Depends(config.get_config),
) -> Service:
    return Service(
        db,
        config.SECRET_KEY,
        config.ALGORITHM,
        timedelta(minutes=config.TOKEN_EXPIRE_MINUTES),
    )


_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authorize")


async def get_current_user(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(_oauth2_scheme),
    config: config.Config = Depends(config.get_config),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        timestamp = payload.get("exp")
        if timestamp is None or not isinstance(timestamp, float):
            raise credentials_exception

        exp = datetime.fromtimestamp(timestamp, timezone.utc)
        if datetime.now(timezone.utc) > exp:
            raise credentials_exception

        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        user = await db.get(models.User, int(user_id))
        if user is None:
            raise credentials_exception

        return user

    except jose.JWTError:
        raise credentials_exception
