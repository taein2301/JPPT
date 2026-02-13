"""FastAPI 실행 유틸리티.

이 모듈은 Typer의 api 명령에서 FastAPI 애플리케이션을 실행합니다.
"""

from loguru import logger

from src.utils.config import Settings


def run_api_server(
    settings: Settings,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """FastAPI 서버를 실행합니다.

    Args:
        settings: 애플리케이션 설정
        host: 바인딩할 호스트
        port: 바인딩할 포트
        reload: 개발용 코드 리로드 활성화 여부
    """
    # import inside function to keep CLI/API tests runnable even if optional deps
    # are not installed until API execution is actually requested.
    import uvicorn

    from src.api.app import create_api_app

    api_app = create_api_app(settings)

    logger.info(f"Starting API server for {settings.app.name} on {host}:{port}")
    uvicorn.run(
        api_app,
        host=host,
        port=port,
        log_level=settings.logging.level.lower(),
        reload=reload,
    )
