"""FastAPI 애플리케이션 정의.

이 모듈은 템플릿의 공통 설정을 기반으로 API 라우트를 제공합니다.
"""

from collections.abc import AsyncIterator
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from src.utils.config import Settings
from src.utils.exceptions import AppException, ValidationError


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


class ErrorResponse(BaseModel):
    """공통 에러 응답 모델."""

    detail: str
    code: str
    request_id: str


def _exception_code(exc: Exception) -> str:
    """예외 클래스를 snake_case 코드로 변환합니다."""
    name = exc.__class__.__name__
    chars: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def _request_id(request: Request) -> str:
    """요청 ID를 반환합니다."""
    return getattr(request.state, "request_id", str(uuid4()))


def _create_system_router(settings: Settings) -> APIRouter:
    """시스템 라우터를 생성합니다."""
    router = APIRouter(tags=["system"])

    @router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """서비스 상태를 조회합니다."""
        return HealthResponse(
            status="ok",
            app=settings.app.name,
            version=settings.app.version,
            debug=settings.app.debug,
        )

    @router.get("/ready", response_model=HealthResponse)
    async def ready_check() -> HealthResponse:
        """서비스 준비 상태를 조회합니다."""
        return HealthResponse(
            status="ready",
            app=settings.app.name,
            version=settings.app.version,
            debug=settings.app.debug,
        )

    return router


def _create_jobs_router() -> APIRouter:
    """작업 라우터를 생성합니다."""
    router = APIRouter(prefix="/jobs", tags=["jobs"])

    @router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
    async def create_job(request: JobCreateRequest) -> JobResponse:
        """간단한 샘플 작업을 등록합니다."""
        if request.name.strip().lower() == "error":
            raise ValidationError("Reserved job name")

        logger.info("Received job request: {}", request.name)
        return JobResponse(job_id=str(uuid4()), name=request.name, status="queued")

    return router


def create_api_app(settings: Settings) -> FastAPI:
    """FastAPI 애플리케이션 객체를 생성합니다."""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """애플리케이션 수명주기를 관리합니다."""
        app.state.ready = True
        yield

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=settings.app.debug,
        root_path=settings.api.root_path,
        docs_url="/docs" if settings.api.docs_enabled else None,
        redoc_url="/redoc" if settings.api.docs_enabled else None,
        openapi_url="/openapi.json" if settings.api.docs_enabled else None,
        lifespan=lifespan,
    )

    if settings.api.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if settings.api.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.api.trusted_hosts,
        )

    @app.middleware("http")
    async def add_request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """요청 ID를 컨텍스트에 주입합니다."""
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        """애플리케이션 예외를 공통 포맷으로 반환합니다."""
        status_code = status.HTTP_400_BAD_REQUEST if isinstance(exc, ValidationError) else 500
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                detail=str(exc),
                code=_exception_code(exc),
                request_id=_request_id(request),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """FastAPI 요청 검증 오류를 공통 포맷으로 반환합니다."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                detail="Request validation failed",
                code="request_validation_error",
                request_id=_request_id(request),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        """예상하지 못한 예외를 공통 포맷으로 반환합니다."""
        logger.exception("Unhandled API error on {}", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="Internal server error",
                code="internal_server_error",
                request_id=_request_id(request),
            ).model_dump(),
        )

    system_router = _create_system_router(settings)
    jobs_router = _create_jobs_router()
    app.include_router(system_router)
    app.include_router(jobs_router)

    return app
