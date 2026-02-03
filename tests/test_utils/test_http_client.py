import pytest

from src.jppt.utils.exceptions import HttpClientError
from src.jppt.utils.http_client import HttpClient


@pytest.mark.asyncio
async def test_http_client_get() -> None:
    async with HttpClient(base_url="https://httpbin.org") as client:
        response = await client.get("/get")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data


@pytest.mark.asyncio
async def test_http_client_timeout() -> None:
    async with HttpClient(timeout=0.001) as client:
        with pytest.raises(HttpClientError):
            await client.get("https://httpbin.org/delay/10")
