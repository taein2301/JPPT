"""FastAPI 애플리케이션 정의.

이 모듈은 템플릿의 공통 설정을 기반으로 API 라우트를 제공합니다.
"""

from uuid import uuid4
from typing import Any

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel
from pydantic import Field

from src.utils.config import Settings


class HealthResponse(BaseModel):
    """서비스 상태 응답 모델."""

    status: str
    app: str
    version: str
    debug: bool


class JobCreateRequest(BaseModel):
    """배치 작업 요청 모델."""

    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    """작업 등록 응답 모델."""

    job_id: str
    name: str
    status: str


def create_api_app(settings: Settings) -> FastAPI:
    """FastAPI 애플리케이션 객체를 생성합니다."""
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=settings.app.debug,
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health_check() -> HealthResponse:
        """서비스 상태를 조회합니다."""
        return HealthResponse(
            status="ok",
            app=settings.app.name,
            version=settings.app.version,
            debug=settings.app.debug,
        )

    @app.post("/jobs", response_model=JobResponse, status_code=201, tags=["jobs"])
    async def create_job(request: JobCreateRequest) -> JobResponse:
        """간단한 샘플 작업을 등록합니다."""
        logger.info(f"Received job request: {request.name}")
        return JobResponse(job_id=str(uuid4()), name=request.name, status="queued")

    return app
