import re

from pydantic import BaseModel, Field
from app.models.models import VacancyStatus

_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z ]*$")
_ALNUM_STR_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")

_NAME_FIELD = Field(pattern=_NAME_REGEX)
_PASSWORD_FIELD = Field(pattern=_ALNUM_STR_REGEX, min_length=8)
_LOGIN_FIELD = Field(pattern=_ALNUM_STR_REGEX, min_length=1)
_ID_FIELD = Field(ge=0)


class RegisterRequest(BaseModel):
    login: str = _LOGIN_FIELD
    password: str = _PASSWORD_FIELD


class AuthorizeResponse(BaseModel):
    access_token: str
    token_type: str


class ChangePasswordRequest(BaseModel):
    old_password: str = _PASSWORD_FIELD
    new_password: str = _PASSWORD_FIELD


class Vacancy(BaseModel):
    title: str = _NAME_FIELD
    description: str
    status: VacancyStatus
    position_id: int = _ID_FIELD
    category_id: int = _ID_FIELD


class CreateVacancyRequest(BaseModel):
    title: str = _NAME_FIELD
    description: str
    position_id: int = _ID_FIELD
    category_id: int = _ID_FIELD


class CreateVacancyResponse(BaseModel):
    vacancy_id: int = _ID_FIELD


class UpdateVacancyRequest(BaseModel):
    title: str | None = Field(pattern=_NAME_REGEX, default=None)
    description: str | None = None
    position_id: int | None = Field(ge=0, default=None)
    category_id: int | None = Field(ge=0, default=None)


class CloseVacancyRequest(BaseModel):
    vacancy_id: int = _ID_FIELD


class Resume(BaseModel):
    full_name: str = _NAME_FIELD
    title: str = _NAME_FIELD
    contact_info: str = Field(min_length=1)
    description: str
    category_id: int = _ID_FIELD


class CreateResumeRequest(BaseModel):
    resume: Resume


class CreateResumeResponse(BaseModel):
    resume_id: int = _ID_FIELD


class UpdateResumeRequest(BaseModel):
    title: str | None = Field(pattern=_NAME_REGEX, default=None)
    full_name: str | None = Field(pattern=_NAME_REGEX, default=None)
    contact_info: str | None = Field(min_length=1, default=None)
    description: str | None = None
    category_id: int | None = Field(ge=0, default=None)


class AddCategoryRequest(BaseModel):
    name: str


class AddCategoryResponse(BaseModel):
    category_id: int = _ID_FIELD


class GetCategoriesResponse(BaseModel):
    categories: dict[int, str]


class AddPositionRequest(BaseModel):
    name: str = _NAME_FIELD


class AddPositionResponse(BaseModel):
    position_id: int = _ID_FIELD


class GetPositionsResponse(BaseModel):
    positions: dict[int, str]


class GetVacanciesResponse(BaseModel):
    vacancies: dict[int, Vacancy]


class GetResumesResponse(BaseModel):
    resumes: dict[int, Resume]
