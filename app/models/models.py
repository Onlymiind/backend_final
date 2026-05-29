import enum

from sqlalchemy import Enum, Text, BINARY, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TableWithId(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)


class User(TableWithId):
    __tablename__ = "users"

    login: Mapped[str] = mapped_column(Text, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)


class Category(TableWithId):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(Text, unique=True, index=True)


class Position(TableWithId):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(Text, unique=True, index=True)


class VacancyStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Vacancy(TableWithId):
    __tablename__ = "vacancies"

    title: Mapped[str] = mapped_column(Text, index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[VacancyStatus] = mapped_column(
        Enum(VacancyStatus), default=VacancyStatus.OPEN, index=True
    )

    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)

    position: Mapped[Position] = relationship("Position", lazy="joined")
    category: Mapped[Category] = relationship("Category", lazy="joined")


class ResumeStatus(str, enum.Enum):
    PROCESSING = "processing"
    HIRED = "hired"
    REJECTED = "rejected"


class Resume(TableWithId):
    __tablename__ = "resumes"

    full_name: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    contact_info: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus), default=ResumeStatus.PROCESSING
    )

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[Category] = relationship("Category", lazy="joined")
