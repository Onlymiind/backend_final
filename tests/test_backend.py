import pytest
import httpx2

from app.schemas import schemas
from app.models import models
from fastapi.testclient import TestClient


def get_auth_token(test_client, username: str = "abc", password: str = "1" * 8) -> str:
    assert (
        test_client.post(
            "/register", json={"login": username, "password": password}
        ).status_code
        == 204
    )

    result: httpx2.Response = test_client.post(
        "/authorize", data={"username": username, "password": password}
    )
    assert result.status_code == 200
    response = schemas.AuthorizeResponse.model_validate(result.json(), by_name=True)
    return response.access_token


def add_position(test_client: TestClient, token: str, name: str) -> int:
    result = test_client.post(
        "/position/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.AddPositionRequest(name=name).model_dump(),
    )

    assert result.status_code == 200
    response = schemas.AddPositionResponse.model_validate(result.json(), by_name=True)
    return response.position_id


def add_category(test_client: TestClient, token: str, name: str) -> int:
    result = test_client.post(
        "/category/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.AddCategoryRequest(name=name).model_dump(),
    )

    assert result.status_code == 200
    response = schemas.AddCategoryResponse.model_validate(result.json(), by_name=True)
    return response.category_id


def add_vacancy(
    test_client: TestClient,
    token: str,
    title: str,
    description: str,
    position_id: int,
    category_id: int,
) -> int:

    result = test_client.post(
        "/vacancy/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.CreateVacancyRequest(
            title=title,
            description=description,
            position_id=position_id,
            category_id=category_id,
        ).model_dump(),
    )

    assert result.status_code == 200
    response = schemas.CreateVacancyResponse.model_validate(result.json(), by_name=True)
    return response.vacancy_id


def add_resume(test_client: TestClient, token: str, resume: schemas.Resume) -> int:
    result = test_client.post(
        "/resume/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.CreateResumeRequest(resume=resume).model_dump(),
    )
    assert result.status_code == 200
    response = schemas.CreateResumeResponse.model_validate(result.json(), by_name=True)
    return response.resume_id


@pytest.mark.parametrize(
    ["login", "password", "expected_code"],
    [
        pytest.param("abc", "12345678", 204, id="OK"),
        pytest.param("abc", "12345678", 204, id="OK2"),
        pytest.param("", "12345678", 422, id="InvalidLogin"),
        pytest.param("abc", "1", 422, id="InvalidPassword"),
    ],
)
def test_registration(
    test_client: TestClient, login: str, password: str, expected_code: int
):
    response = test_client.post(
        "/register", json={"login": login, "password": password}
    )

    assert response.status_code == expected_code


def test_duplicate_user(test_client: TestClient):
    assert (
        test_client.post(
            "/register", json={"login": "abc", "password": "1" * 8}
        ).status_code
        == 204
    )

    assert (
        test_client.post(
            "/register", json={"login": "abc", "password": "1" * 8}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    ["login", "password", "expected_code"],
    [
        pytest.param("abc", "1" * 8, 200, id="OK"),
        pytest.param("abc", "12345678", 401, id="WrongPassword"),
        pytest.param("www", "1" * 8, 401, id="MissingUser"),
    ],
)
def test_authorize(
    test_client: TestClient, login: str, password: str, expected_code: int
):
    assert (
        test_client.post(
            "/register", json={"login": "abc", "password": "1" * 8}
        ).status_code
        == 204
    )

    result: httpx2.Response = test_client.post(
        "/authorize", data={"username": login, "password": password}
    )
    assert result.status_code == expected_code
    if expected_code == 200:
        response = schemas.AuthorizeResponse.model_validate(result.json(), by_name=True)
        assert response.access_token
        assert response.token_type == "bearer"


@pytest.mark.parametrize(
    ["old_password", "expected_code"],
    [
        pytest.param("1" * 8, 204, id="OK"),
        pytest.param("12345678", 401, id="WrongPassword"),
    ],
)
def test_change_password(
    test_client: TestClient, old_password: str, expected_code: int
):
    token = get_auth_token(test_client, "abc", "1" * 8)

    result = test_client.post(
        "/change_password",
        headers={"Authorization": f"bearer {token}"},
        json={"old_password": old_password, "new_password": "00000000"},
    )

    assert result.status_code == expected_code


def test_refresh_token(test_client: TestClient):
    token = get_auth_token(test_client, "abc", "1" * 8)

    result = test_client.post(
        "/auth/refresh", headers={"Authorization": f"bearer {token}"}
    )

    assert result.status_code == 200
    response = schemas.AuthorizeResponse.model_validate(result.json(), by_name=True)
    assert response.access_token
    assert response.token_type == "bearer"


def test_adding_category(test_client):
    token = get_auth_token(test_client)

    result = test_client.post(
        "/category/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.AddCategoryRequest(name="some category").model_dump(),
    )

    assert result.status_code == 200
    response = schemas.AddCategoryResponse.model_validate(result.json(), by_name=True)
    assert response.category_id

    result = test_client.get(
        "/category/all", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200

    categories = schemas.GetCategoriesResponse.model_validate(
        result.json(), by_name=True
    )
    assert len(categories.categories) == 1
    assert categories.categories[response.category_id] == "some category"


def test_adding_position(test_client):
    token = get_auth_token(test_client)

    result = test_client.post(
        "/position/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.AddPositionRequest(name="some position").model_dump(),
    )

    assert result.status_code == 200
    response = schemas.AddPositionResponse.model_validate(result.json(), by_name=True)
    assert response.position_id

    result = test_client.get(
        "/position/all", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200

    positions = schemas.GetPositionsResponse.model_validate(result.json(), by_name=True)
    assert len(positions.positions) == 1
    assert positions.positions[response.position_id] == "some position"


def test_adding_vacancy(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")
    position = add_position(test_client, token, "some position")

    vacancy = schemas.Vacancy(
        title="some title",
        description="some description",
        status=models.VacancyStatus.OPEN,
        position_id=position,
        category_id=category,
    )

    result = test_client.post(
        "/vacancy/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.CreateVacancyRequest(
            title=vacancy.title,
            description=vacancy.description,
            position_id=vacancy.position_id,
            category_id=vacancy.category_id,
        ).model_dump(),
    )

    assert result.status_code == 200
    response = schemas.CreateVacancyResponse.model_validate(result.json(), by_name=True)
    assert response.vacancy_id

    result = test_client.get(
        f"/vacancy/{response.vacancy_id}", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200
    assert schemas.Vacancy.model_validate(result.json(), by_name=True) == vacancy

    result = test_client.get(
        "/vacancy/all", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200
    vacancies = schemas.GetVacanciesResponse.model_validate(result.json(), by_name=True)
    assert len(vacancies.vacancies) == 1
    assert vacancies.vacancies[response.vacancy_id] == vacancy


@pytest.mark.parametrize(
    ["add_status", "status_fails"],
    [pytest.param(True, False), pytest.param(True, True), pytest.param(False, False)],
)
@pytest.mark.parametrize(
    ["add_position_id", "position_id_fails"],
    [pytest.param(True, False), pytest.param(True, True), pytest.param(False, False)],
)
@pytest.mark.parametrize(
    ["add_category_id", "category_id_fails"],
    [pytest.param(True, False), pytest.param(True, True), pytest.param(False, False)],
)
def test_filtering_vacancies(
    test_client: TestClient,
    add_status: bool,
    status_fails: bool,
    add_position_id: bool,
    position_id_fails: bool,
    add_category_id: bool,
    category_id_fails: bool,
):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")
    position = add_position(test_client, token, "some position")

    vacancy = schemas.Vacancy(
        title="some title",
        description="some description",
        status=models.VacancyStatus.OPEN,
        position_id=position,
        category_id=category,
    )
    vacancy_id = add_vacancy(
        test_client, token, vacancy.title, vacancy.description, position, category
    )

    params = {
        "status": ("closed" if status_fails else "open") if add_status else None,
        "position_id": ((position + 1) if position_id_fails else position)
        if add_position_id
        else None,
        "category_id": ((category + 1) if category_id_fails else category)
        if add_category_id
        else None,
    }
    result = test_client.get(
        "/vacancy/all",
        headers={"Authorization": f"bearer {token}"},
        params={k: v for k, v in params.items() if v},
    )
    assert result.status_code == 200
    vacancies = schemas.GetVacanciesResponse.model_validate(result.json(), by_name=True)
    if status_fails or position_id_fails or category_id_fails:
        assert len(vacancies.vacancies) == 0
    else:
        assert len(vacancies.vacancies) == 1
        assert vacancies.vacancies[vacancy_id] == vacancy


@pytest.mark.parametrize("add_title", [True, False])
@pytest.mark.parametrize("add_description", [True, False])
@pytest.mark.parametrize("add_position_id", [True, False])
@pytest.mark.parametrize("add_category_id", [True, False])
def test_updating_vacancy(
    test_client,
    add_title: bool,
    add_description: bool,
    add_category_id: bool,
    add_position_id: bool,
):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")
    position = add_position(test_client, token, "some position")

    other_category = add_category(test_client, token, "some other category")
    other_position = add_position(test_client, token, "some other position")

    vacancy = schemas.Vacancy(
        title="some title",
        description="some description",
        status=models.VacancyStatus.OPEN,
        position_id=position,
        category_id=category,
    )
    vacancy_id = add_vacancy(
        test_client, token, vacancy.title, vacancy.description, position, category
    )

    result = test_client.patch(
        f"/vacancy/update/{vacancy_id}",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.UpdateVacancyRequest(
            title="other title" if add_title else None,
            description="other description" if add_description else None,
            category_id=other_category if add_category_id else None,
            position_id=other_position if add_position_id else None,
        ).model_dump(),
    )

    assert result.status_code == 204

    updated = schemas.Vacancy.model_validate(
        test_client.get(
            f"/vacancy/{vacancy_id}", headers={"Authorization": f"bearer {token}"}
        ).json(),
        by_name=True,
    )

    assert updated.title == vacancy.title if not add_title else "other title"
    assert (
        updated.description == vacancy.description
        if not add_description
        else "other description"
    )
    assert (
        updated.category_id == vacancy.category_id
        if not add_category_id
        else other_category
    )
    assert (
        updated.position_id == vacancy.position_id
        if not add_position_id
        else other_position
    )


def test_closing_vacancy(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")
    position = add_position(test_client, token, "some position")

    vacancy = schemas.Vacancy(
        title="some title",
        description="some description",
        status=models.VacancyStatus.CLOSED,
        position_id=position,
        category_id=category,
    )
    vacancy_id = add_vacancy(
        test_client, token, vacancy.title, vacancy.description, position, category
    )

    result = test_client.post(
        "/vacancy/close",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.CloseVacancyRequest(vacancy_id=vacancy_id).model_dump(),
    )

    assert result.status_code == 204

    updated = schemas.Vacancy.model_validate(
        test_client.get(
            f"/vacancy/{vacancy_id}", headers={"Authorization": f"bearer {token}"}
        ).json(),
        by_name=True,
    )
    assert updated == vacancy


def test_deleting_vacancy(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")
    position = add_position(test_client, token, "some position")

    vacancy = schemas.Vacancy(
        title="some title",
        description="some description",
        status=models.VacancyStatus.CLOSED,
        position_id=position,
        category_id=category,
    )
    vacancy_id = add_vacancy(
        test_client, token, vacancy.title, vacancy.description, position, category
    )

    result = test_client.delete(
        f"/vacancy/delete/{vacancy_id}", headers={"Authorization": f"bearer {token}"}
    )

    assert result.status_code == 204

    result = test_client.get(
        f"/vacancy/{vacancy_id}", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 404


def test_adding_resume(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")

    resume = schemas.Resume(
        full_name="John Doe",
        title="some title",
        description="some description",
        contact_info="some info",
        category_id=category,
    )

    result = test_client.post(
        "/resume/new",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.CreateResumeRequest(resume=resume).model_dump(),
    )
    assert result.status_code == 200
    response = schemas.CreateResumeResponse.model_validate(result.json(), by_name=True)
    assert response.resume_id

    result = test_client.get(
        f"/resume/{response.resume_id}", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200
    assert schemas.Resume.model_validate(result.json(), by_name=True) == resume

    result = test_client.get(
        "/resume/all", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200
    resumes = schemas.GetResumesResponse.model_validate(result.json(), by_name=True)
    assert len(resumes.resumes) == 1
    assert resumes.resumes[response.resume_id] == resume


def test_updating_resume(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")

    other_category = add_category(test_client, token, "other category")

    resume = schemas.Resume(
        full_name="John Doe",
        title="some title",
        description="some description",
        contact_info="some info",
        category_id=category,
    )

    resume_id = add_resume(test_client, token, resume)

    result = test_client.patch(
        f"/resume/update/{resume_id}",
        headers={"Authorization": f"bearer {token}"},
        json=schemas.UpdateResumeRequest(
            title="other title",
            full_name="Other Name",
            contact_info="other contact",
            description="other description",
            category_id=other_category,
        ).model_dump(),
    )

    assert result.status_code == 204

    result = test_client.get(
        f"/resume/{resume_id}", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 200
    assert schemas.Resume.model_validate(result.json(), by_name=True) == schemas.Resume(
        title="other title",
        full_name="Other Name",
        contact_info="other contact",
        description="other description",
        category_id=other_category,
    )


def test_deleting_resume(test_client: TestClient):
    token = get_auth_token(test_client)
    category = add_category(test_client, token, "some category")

    resume = schemas.Resume(
        full_name="John Doe",
        title="some title",
        description="some description",
        contact_info="some info",
        category_id=category,
    )

    resume_id = add_resume(test_client, token, resume)

    result = test_client.delete(
        f"/resume/delete/{resume_id}", headers={"Authorization": f"bearer {token}"}
    )

    assert result.status_code == 204

    result = test_client.get(
        f"/resume/{resume_id}", headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 404


@pytest.mark.parametrize(
    ["path", "method", "body"],
    [
        pytest.param("/vacancy/1234", "get", None),
        pytest.param("/resume/1234", "get", None),
        pytest.param(
            "/vacancy/update/1234", "patch", schemas.UpdateVacancyRequest().model_dump()
        ),
        pytest.param(
            "/resume/update/1234", "patch", schemas.UpdateResumeRequest().model_dump()
        ),
        pytest.param("/vacancy/delete/1234", "delete", None),
        pytest.param("/resume/delete/1234", "delete", None),
    ],
)
def test_not_found(test_client: TestClient, path, method, body):
    token = get_auth_token(test_client)

    result = test_client.request(
        method, path, json=body, headers={"Authorization": f"bearer {token}"}
    )
    assert result.status_code == 404
