"""FastAPI 실행 유틸리티.

이 모듈은 Typer의 api 명령에서 FastAPI 애플리케이션을 실행합니다.
"""

from loguru import logger

from src.utils.config import Settings


def run_api_server(
    settings: Settings,
    host: str | None = None,
    port: int | None = None,
    reload: bool | None = None,
    log_level: str | None = None,
) -> None:
    """FastAPI 서버를 실행합니다.

    Args:
        settings: 애플리케이션 설정
        host: 바인딩할 호스트
        port: 바인딩할 포트
        reload: 개발용 코드 리로드 활성화 여부
        log_level: uvicorn에 전달할 로그 레벨
    """
    # import inside function to keep CLI/API tests runnable even if optional deps
    # are not installed until API execution is actually requested.
    import uvicorn

    from src.api.app import create_api_app

    api_app = create_api_app(settings)
    effective_host = settings.api.host if host is None else host
    effective_port = settings.api.port if port is None else port
    effective_reload = settings.api.reload if reload is None else reload
    effective_log_level = settings.logging.level if log_level is None else log_level

    logger.info(
        "Starting API server for {} on {}:{}",
        settings.app.name,
        effective_host,
        effective_port,
    )
    uvicorn.run(
        api_app,
        host=effective_host,
        port=effective_port,
        log_level=effective_log_level.lower(),
        reload=effective_reload,
    )
