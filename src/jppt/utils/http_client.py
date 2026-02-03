"""HTTP client wrapper using httpx."""

from typing import Any

import httpx
from loguru import logger

from src.jppt.utils.exceptions import HttpClientError


class HttpClient:
    """
    Async HTTP client with timeout and retry support.

    Example:
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
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Total timeout for requests in seconds
            connect_timeout: Connection timeout in seconds
        """
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(timeout=timeout, connect=connect_timeout)

    async def __aenter__(self) -> "HttpClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Send GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            HttpClientError: If request fails
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
        """
        Send POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            HttpClientError: If request fails
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
