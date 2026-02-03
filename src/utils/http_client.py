"""httpx를 사용한 HTTP 클라이언트 래퍼.

이 모듈은 타임아웃, 재시도, 에러 처리를 지원하는 비동기 HTTP 클라이언트를 제공합니다.
"""

from typing import Any

import httpx
from loguru import logger

from src.utils.exceptions import HttpClientError


class HttpClient:
    """타임아웃 및 재시도를 지원하는 비동기 HTTP 클라이언트.

    컨텍스트 매니저로 사용하여 자동으로 연결을 관리합니다.
    모든 요청은 자동으로 리다이렉트를 따라가며, 에러 시 예외를 발생시킵니다.

    사용 예시:
        async with HttpClient(base_url="https://api.example.com") as client:
            response = await client.get("/endpoint")
            data = response.json()
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
    ) -> None:
        """HTTP 클라이언트를 초기화합니다.

        Args:
            base_url: 모든 요청의 기본 URL
            timeout: 요청 전체 타임아웃 (초)
            connect_timeout: 연결 타임아웃 (초)
        """
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(timeout=timeout, connect=connect_timeout)

    async def __aenter__(self) -> "HttpClient":
        """비동기 컨텍스트 매니저 진입."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """비동기 컨텍스트 매니저 종료 및 연결 닫기."""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET 요청을 전송합니다.

        Args:
            url: 요청 URL
            params: 쿼리 파라미터
            headers: 요청 헤더

        Returns:
            HTTP 응답 객체

        Raises:
            HttpClientError: 요청 실패 시
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.debug(f"GET {url} params={params}")
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP GET failed: {url} - {e}")
            raise HttpClientError(f"HTTP GET failed: {e}") from e

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """POST 요청을 전송합니다.

        Args:
            url: 요청 URL
            json: JSON 바디
            data: 폼 데이터
            headers: 요청 헤더

        Returns:
            HTTP 응답 객체

        Raises:
            HttpClientError: 요청 실패 시
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.debug(f"POST {url}")
            response = await self._client.post(url, json=json, data=data, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP POST failed: {url} - {e}")
            raise HttpClientError(f"HTTP POST failed: {e}") from e
