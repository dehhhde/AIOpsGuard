"""Prometheus 客户端单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from infrastructure.external.prometheus_client import PrometheusClient


class MockResponse:
    """Mock HTTP 响应"""
    
    def __init__(self, json_data: dict, status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self) -> dict:
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                message=f"HTTP {self.status_code}",
                request=MagicMock(),
                response=self
            )


@pytest.fixture
def mock_http_client():
    """Mock HTTP 客户端"""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client


@pytest.mark.asyncio
async def test_prometheus_client_initialization():
    """测试客户端初始化"""
    client = PrometheusClient(
        base_url="http://test-prometheus:9090",
        timeout=10.0
    )
    
    assert client.base_url == "http://test-prometheus:9090"
    assert client.timeout == 10.0


@pytest.mark.asyncio
async def test_query_success(mock_http_client):
    """测试成功的即时查询"""
    # 准备 Mock 响应
    mock_response = MockResponse({
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "job": "prometheus"},
                    "value": [1704873600, "1"]
                }
            ]
        }
    })
    
    # 配置 Mock
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    # 执行测试
    async with PrometheusClient() as client:
        result = await client.query("up")
    
    # 验证
    assert result["status"] == "success"
    assert result["data"]["resultType"] == "vector"
    assert len(result["data"]["result"]) == 1
    
    # 验证调用
    mock_instance.get.assert_called_once_with(
        "/api/v1/query",
        params={"query": "up"}
    )


@pytest.mark.asyncio
async def test_query_with_time(mock_http_client):
    """测试带时间参数的查询"""
    mock_response = MockResponse({
        "status": "success",
        "data": {"resultType": "vector", "result": []}
    })
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        result = await client.query("up", time="2025-01-10T10:00:00Z")
    
    assert result["status"] == "success"
    
    # 验证参数
    mock_instance.get.assert_called_once_with(
        "/api/v1/query",
        params={"query": "up", "time": "2025-01-10T10:00:00Z"}
    )


@pytest.mark.asyncio
async def test_query_range_success(mock_http_client):
    """测试成功的范围查询"""
    mock_response = MockResponse({
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": "cpu_usage"},
                    "values": [
                        [1704873600, "0.5"],
                        [1704873660, "0.6"]
                    ]
                }
            ]
        }
    })
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        result = await client.query_range(
            query="cpu_usage",
            start="2025-01-10T10:00:00Z",
            end="2025-01-10T11:00:00Z",
            step="1m"
        )
    
    assert result["status"] == "success"
    assert result["data"]["resultType"] == "matrix"
    assert len(result["data"]["result"]) == 1
    
    # 验证参数
    mock_instance.get.assert_called_once_with(
        "/api/v1/query_range",
        params={
            "query": "cpu_usage",
            "start": "2025-01-10T10:00:00Z",
            "end": "2025-01-10T11:00:00Z",
            "step": "1m"
        }
    )


@pytest.mark.asyncio
async def test_series_success(mock_http_client):
    """测试序列查询"""
    mock_response = MockResponse({
        "status": "success",
        "data": [
            {"__name__": "up", "job": "prometheus", "instance": "localhost:9090"},
            {"__name__": "up", "job": "node", "instance": "localhost:9100"}
        ]
    })
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        result = await client.series(
            match=["up"],
            start="2025-01-10T10:00:00Z"
        )
    
    assert result["status"] == "success"
    assert len(result["data"]) == 2
    
    # 验证参数
    mock_instance.get.assert_called_once_with(
        "/api/v1/series",
        params={
            "match[]": ["up"],
            "start": "2025-01-10T10:00:00Z"
        }
    )


@pytest.mark.asyncio
async def test_health_success(mock_http_client):
    """测试健康检查成功"""
    mock_response = MockResponse({}, status_code=200)
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        health = await client.health()
    
    assert health["is_healthy"] is True
    
    mock_instance.get.assert_called_once_with("/-/healthy")


@pytest.mark.asyncio
async def test_health_failure(mock_http_client):
    """测试健康检查失败"""
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        health = await client.health()
    
    assert health["is_healthy"] is False


@pytest.mark.asyncio
async def test_query_http_error(mock_http_client):
    """测试 HTTP 错误处理"""
    mock_response = MockResponse(
        {"status": "error", "error": "Bad query"},
        status_code=400
    )
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.query("invalid query")


@pytest.mark.asyncio
async def test_query_request_error(mock_http_client):
    """测试网络请求错误"""
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(
        side_effect=httpx.RequestError("Network error")
    )
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        with pytest.raises(httpx.RequestError):
            await client.query("up")


@pytest.mark.asyncio
async def test_labels_success(mock_http_client):
    """测试获取标签列表"""
    mock_response = MockResponse({
        "status": "success",
        "data": ["__name__", "job", "instance"]
    })
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        result = await client.labels()
    
    assert result["status"] == "success"
    assert "__name__" in result["data"]
    assert "job" in result["data"]


@pytest.mark.asyncio
async def test_label_values_success(mock_http_client):
    """测试获取标签值"""
    mock_response = MockResponse({
        "status": "success",
        "data": ["prometheus", "node_exporter"]
    })
    
    mock_instance = AsyncMock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_http_client.return_value.__aenter__.return_value = mock_instance
    
    async with PrometheusClient() as client:
        result = await client.label_values("job")
    
    assert result["status"] == "success"
    assert "prometheus" in result["data"]
    assert "node_exporter" in result["data"]
    
    mock_instance.get.assert_called_once_with("/api/v1/label/job/values")


@pytest.mark.asyncio
async def test_context_manager():
    """测试上下文管理器"""
    client = PrometheusClient()
    
    # 未进入上下文前，client 为 None
    assert client._client is None
    
    async with client as c:
        # 进入上下文后，client 被创建
        assert c._client is not None
        assert isinstance(c._client, httpx.AsyncClient)
    
    # 退出上下文后，client 被关闭（这里无法直接验证，但不应报错）
