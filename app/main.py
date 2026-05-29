from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import routers


def create_app() -> FastAPI:
    app = FastAPI(
        title="backend",
        version="0.1.0",
        description="HR Vacancy Management System API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=routers.router)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
