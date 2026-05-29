import pydantic
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import models
from app.schemas import schemas
from app.core import database


class Service:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_categories(self) -> schemas.GetCategoriesResponse:
        result = await self.db.execute(select(models.Category))
        categories = result.scalars().all()
        return schemas.GetCategoriesResponse(
            categories={category.id: category.name for category in categories}
        )

    async def add_category(
        self, request: schemas.AddCategoryRequest
    ) -> schemas.AddCategoryResponse:
        result = await self.db.execute(
            select(models.Category).where(models.Category.name == request.name)
        )
        if result.scalars().first():
            raise HTTPException(status_code=409, detail="Category already exists")

        return schemas.AddCategoryResponse(
            category_id=await self._add_value(
                request, schemas.AddCategoryRequest, models.Category
            )
        )

    async def get_positions(self) -> schemas.GetPositionsResponse:
        result = await self.db.execute(select(models.Position))
        positions = result.scalars().all()
        return schemas.GetPositionsResponse(
            positions={position.id: position.name for position in positions}
        )

    async def add_position(
        self, request: schemas.AddPositionRequest
    ) -> schemas.AddPositionResponse:
        result = await self.db.execute(
            select(models.Position).where(models.Position.name == request.name)
        )
        if result.scalars().first():
            raise HTTPException(status_code=409, detail="Position already exists")

        return schemas.AddPositionResponse(
            position_id=await self._add_value(
                request, schemas.AddPositionRequest, models.Position
            )
        )

    async def get_vacancies(
        self,
        status: models.VacancyStatus | None = None,
        position_id: int | None = None,
        category_id: int | None = None,
    ) -> schemas.GetVacanciesResponse:
        filters = []
        if status:
            filters.append(models.Vacancy.status == status)
        if position_id is not None:
            filters.append(models.Vacancy.position_id == position_id)
        if category_id is not None:
            filters.append(models.Vacancy.category_id == category_id)

        result = await self.db.execute(select(models.Vacancy).where(*filters))

        vacancies = result.scalars().all()
        return schemas.GetVacanciesResponse(
            vacancies={
                vacancy.id: schemas.Vacancy.model_validate(
                    vacancy, from_attributes=True
                )
                for vacancy in vacancies
            }
        )

    async def get_vacancy(self, vacancy_id: int) -> schemas.Vacancy:
        result = await self.db.execute(
            select(models.Vacancy).where(models.Vacancy.id == vacancy_id)
        )
        vacancy = result.scalars().one_or_none()
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        return schemas.Vacancy.model_validate(vacancy, from_attributes=True)

    async def create_vacancy(
        self, request: schemas.CreateVacancyRequest
    ) -> schemas.CreateVacancyResponse:

        if not await self._has_entity(models.Position, request.position_id):
            raise HTTPException(status_code=404, detail="Position not found")
        if not await self._has_entity(models.Category, request.category_id):
            raise HTTPException(status_code=404, detail="Category not found")

        return schemas.CreateVacancyResponse(
            vacancy_id=await self._add_value(
                request, schemas.CreateVacancyRequest, models.Vacancy
            )
        )

    async def update_vacancy(
        self, request: schemas.UpdateVacancyRequest, vacancy_id: int
    ) -> None:
        if request.category_id is not None and not await self._has_entity(
            models.Category, request.category_id
        ):
            raise HTTPException(status_code=404, detail="Category not found")
        if request.position_id is not None and not await self._has_entity(
            models.Position, request.position_id
        ):
            raise HTTPException(status_code=404, detail="Position not found")

        vacancy = await self.db.get(models.Vacancy, vacancy_id)
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        await self._update_value(vacancy, request, schemas.UpdateVacancyRequest)

    async def close_vacancy(self, request: schemas.CloseVacancyRequest) -> None:
        vacancy = await self.db.get(models.Vacancy, request.vacancy_id)
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        vacancy.status = models.VacancyStatus.CLOSED
        await self.db.commit()

    async def delete_vacancy(self, vacancy_id: int) -> None:
        await self._delete_by_id(models.Vacancy, vacancy_id, "Vanancy")

    async def get_resumes(
        self,
        status: models.ResumeStatus | None = None,
        category_id: int | None = None,
    ) -> schemas.GetResumesResponse:
        filters = []
        if status is not None:
            filters.append(models.Resume.status == status)
        if category_id is not None:
            filters.append(models.Resume.category_id == category_id)
        result = await self.db.execute(select(models.Resume).where(*filters))
        resumes = result.scalars().all()

        return schemas.GetResumesResponse(
            resumes={
                resume.id: schemas.Resume.model_validate(resume, from_attributes=True)
                for resume in resumes
            }
        )

    async def get_resume(self, resume_id: int) -> schemas.Resume:
        resume = await self.db.get(models.Resume, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return schemas.Resume.model_validate(resume, from_attributes=True)

    async def create_resume(
        self, request: schemas.CreateResumeRequest
    ) -> schemas.CreateResumeResponse:
        new_resume = request.resume
        if not await self._has_entity(models.Category, new_resume.category_id):
            raise HTTPException(status_code=404, detail="Category not found")

        return schemas.CreateResumeResponse(
            resume_id=await self._add_value(new_resume, schemas.Resume, models.Resume)
        )

    async def update_resume(
        self, request: schemas.UpdateResumeRequest, resume_id: int
    ) -> None:
        if request.category_id is not None and not await self._has_entity(
            models.Category, request.category_id
        ):
            raise HTTPException(status_code=404, detail="Category not found")

        resume = await self.db.get(models.Resume, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        await self._update_value(resume, request, schemas.UpdateResumeRequest)

    async def delete_resume(self, resume_id: int) -> None:
        await self._delete_by_id(models.Resume, resume_id, "Resume")

    async def _has_entity(self, cls: type[models.TableWithId], id: int) -> bool:
        result = await self.db.execute(select(cls).where(cls.id == id))
        return result.scalars().first() is not None

    async def _delete_by_id(
        self, cls: type[models.TableWithId], id: int, entity_name: str
    ):
        entity = await self.db.get(cls, id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        await self.db.delete(entity)
        await self.db.commit()

    async def _update_value(
        self,
        obj: database.Base,
        request: pydantic.BaseModel,
        request_cls: type[pydantic.BaseModel],
    ):
        for name in request_cls.model_fields.keys():
            new_value = getattr(request, name)
            if new_value is not None:
                setattr(obj, name, new_value)
        await self.db.commit()

    async def _add_value(
        self,
        request: pydantic.BaseModel,
        request_cls: type[pydantic.BaseModel],
        table_cls: type[models.TableWithId],
    ) -> int:
        value = table_cls(
            **{name: getattr(request, name) for name in request_cls.model_fields.keys()}
        )
        self.db.add(value)
        await self.db.commit()
        await self.db.refresh(value)
        return value.id


def get_service(db: AsyncSession = Depends(database.get_db)) -> Service:
    return Service(db)
