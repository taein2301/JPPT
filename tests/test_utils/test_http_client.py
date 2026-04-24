import pytest
import httpx

from src.utils.exceptions import HttpClientError
from src.utils.http_client import HttpClient


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


@pytest.mark.asyncio
async def test_http_client_get_includes_exception_type_in_error_message() -> None:
    async with HttpClient() as client:
        assert client._client is not None

        async def raise_timeout(*args, **kwargs):
            raise httpx.ReadTimeout("timed out")

        client._client.get = raise_timeout  # type: ignore[method-assign]

        with pytest.raises(HttpClientError, match="ReadTimeout: timed out"):
            await client.get("https://api.example.com/test")


@pytest.mark.asyncio
async def test_http_client_post_includes_response_body_in_error_message() -> None:
    async with HttpClient() as client:
        assert client._client is not None
        request = httpx.Request("POST", "https://api.example.com/orders")
        response = httpx.Response(
            status_code=400,
            text='{"error":"invalid"}',
            request=request,
        )

        async def raise_bad_request(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "Bad Request",
                request=request,
                response=response,
            )

        client._client.post = raise_bad_request  # type: ignore[method-assign]

        with pytest.raises(
            HttpClientError,
            match='HTTPStatusError: Bad Request - response=\\{"error":"invalid"\\}',
        ):
            await client.post("https://api.example.com/orders", json={"amount": 1})
