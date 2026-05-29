from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm


from app.models.models import User, VacancyStatus, ResumeStatus
from app.schemas.schemas import (
    RegisterRequest,
    AuthorizeResponse,
    ChangePasswordRequest,
    GetCategoriesResponse,
    AddCategoryRequest,
    AddCategoryResponse,
    GetVacanciesResponse,
    CreateVacancyRequest,
    CreateVacancyResponse,
    Vacancy,
    UpdateVacancyRequest,
    CloseVacancyRequest,
    GetResumesResponse,
    Resume,
    CreateResumeRequest,
    CreateResumeResponse,
    UpdateResumeRequest,
    GetPositionsResponse,
    AddPositionRequest,
    AddPositionResponse,
)
from app.services import auth_service, hr_service


router = APIRouter()


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
async def register(
    request: RegisterRequest,
    auth_service: auth_service.Service = Depends(auth_service.get_service),
) -> None:
    await auth_service.register(request)


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: auth_service.Service = Depends(auth_service.get_service),
) -> AuthorizeResponse:
    return await auth_service.authorize(form_data.username, form_data.password)


@router.post("/auth/refresh", response_model=AuthorizeResponse)
async def refresh(
    auth_service: auth_service.Service = Depends(auth_service.get_service),
    user=Depends(auth_service.get_current_user),
) -> AuthorizeResponse:
    return await auth_service.refresh(user)


@router.post("/change_password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    auth_service: auth_service.Service = Depends(auth_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await auth_service.change_password(request, user)


@router.get("/category/all", response_model=GetCategoriesResponse)
async def get_categories(
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> GetCategoriesResponse:
    return await hr_service.get_categories()


@router.post("/category/new", response_model=AddCategoryResponse)
async def create_category(
    request: AddCategoryRequest,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> AddCategoryResponse:
    return await hr_service.add_category(request)


@router.get("/vacancy/all", response_model=GetVacanciesResponse)
async def get_vacancies(
    status: VacancyStatus | None = None,
    position_id: int | None = None,
    category_id: int | None = None,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> GetVacanciesResponse:
    return await hr_service.get_vacancies(
        status=status, position_id=position_id, category_id=category_id
    )


@router.post("/vacancy/new", response_model=CreateVacancyResponse)
async def create_vacancy(
    request: CreateVacancyRequest,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> CreateVacancyResponse:
    return await hr_service.create_vacancy(request)


@router.get("/vacancy/{vacancy_id}", response_model=Vacancy)
async def get_vacancy(
    vacancy_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> Vacancy:
    return await hr_service.get_vacancy(vacancy_id)


@router.patch("/vacancy/update/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_vacancy(
    request: UpdateVacancyRequest,
    vacancy_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await hr_service.update_vacancy(request, vacancy_id)


@router.post("/vacancy/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_vacancy(
    request: CloseVacancyRequest,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await hr_service.close_vacancy(request)


@router.delete("/vacancy/delete/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await hr_service.delete_vacancy(vacancy_id)


@router.get("/resume/all", response_model=GetResumesResponse)
async def get_resumes(
    status: ResumeStatus | None = None,
    category_id: int | None = None,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> GetResumesResponse:
    return await hr_service.get_resumes(
        status=status,
        category_id=category_id,
    )


@router.post("/resume/new", response_model=CreateResumeResponse)
async def create_resume(
    request: CreateResumeRequest,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> CreateResumeResponse:
    return await hr_service.create_resume(request)


@router.get("/resume/{resume_id}", response_model=Resume)
async def get_resume(
    resume_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> Resume:
    return await hr_service.get_resume(resume_id)


@router.patch("/resume/update/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_resume(
    request: UpdateResumeRequest,
    resume_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await hr_service.update_resume(request, resume_id)


@router.delete("/resume/delete/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> None:
    await hr_service.delete_resume(resume_id)


@router.get("/position/all", response_model=GetPositionsResponse)
async def get_positions(
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> GetPositionsResponse:
    return await hr_service.get_positions()


@router.post("/position/new", response_model=AddPositionResponse)
async def create_position(
    request: AddPositionRequest,
    hr_service: hr_service.Service = Depends(hr_service.get_service),
    user: User = Depends(auth_service.get_current_user),
) -> AddPositionResponse:
    return await hr_service.add_position(request)
