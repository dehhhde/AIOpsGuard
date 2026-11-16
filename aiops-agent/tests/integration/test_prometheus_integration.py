"""Prometheus 客户端集成测试

需要运行真实的 Prometheus 实例才能执行这些测试。

启动 Prometheus:
    docker run -d -p 9090:9090 prom/prometheus

运行测试:
    pytest tests/integration/test_prometheus_integration.py -v -m integration
"""
import pytest
from datetime import datetime, timedelta

from infrastructure.external.prometheus_client import PrometheusClient


# 标记为集成测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_prometheus_connection():
    """测试 Prometheus 连接"""
    async with PrometheusClient() as client:
        health = await client.health()
        assert health["is_healthy"] is True, "Prometheus should be healthy"


@pytest.mark.asyncio
async def test_query_up_metric():
    """测试查询 up 指标"""
    async with PrometheusClient() as client:
        result = await client.query("up")
        
        assert result["status"] == "success"
        assert result["data"]["resultType"] == "vector"
        
        # 至少应该有 Prometheus 自己的 up 指标
        assert len(result["data"]["result"]) > 0


@pytest.mark.asyncio
async def test_query_range_scrape_duration():
    """测试范围查询"""
    # 查询最近 5 分钟的数据
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    
    async with PrometheusClient() as client:
        result = await client.query_range(
            query="up",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            step="15s"
        )
        
        assert result["status"] == "success"
        assert result["data"]["resultType"] == "matrix"


@pytest.mark.asyncio
async def test_series_query():
    """测试序列查询"""
    async with PrometheusClient() as client:
        result = await client.series(
            match=["up"],
            start=(datetime.now() - timedelta(hours=1)).isoformat()
        )
        
        assert result["status"] == "success"
        assert len(result["data"]) > 0
        
        # 检查返回的序列包含标签
        first_series = result["data"][0]
        assert "__name__" in first_series
        assert first_series["__name__"] == "up"


@pytest.mark.asyncio
async def test_labels():
    """测试获取标签列表"""
    async with PrometheusClient() as client:
        result = await client.labels()
        
        assert result["status"] == "success"
        assert isinstance(result["data"], list)
        assert "__name__" in result["data"]


@pytest.mark.asyncio
async def test_label_values():
    """测试获取标签值"""
    async with PrometheusClient() as client:
        result = await client.label_values("__name__")
        
        assert result["status"] == "success"
        assert isinstance(result["data"], list)
        # up 是 Prometheus 自带的指标
        assert "up" in result["data"]


@pytest.mark.asyncio
async def test_query_with_invalid_promql():
    """测试无效的 PromQL 查询"""
    async with PrometheusClient() as client:
        result = await client.query("invalid{{{")
        
        # Prometheus 返回错误状态但不抛异常
        assert result["status"] == "error"


@pytest.mark.asyncio
async def test_concurrent_queries():
    """测试并发查询"""
    import asyncio
    
    async def query_up():
        async with PrometheusClient() as client:
            return await client.query("up")
    
    # 并发执行 5 个查询
    results = await asyncio.gather(*[query_up() for _ in range(5)])
    
    # 所有查询都应成功
    for result in results:
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_query_timeout():
    """测试查询超时（使用短超时）"""
    # 使用极短的超时来模拟超时场景
    client = PrometheusClient(timeout=0.001)
    
    async with client:
        with pytest.raises(Exception):  # httpx.TimeoutException
            await client.query("up")
