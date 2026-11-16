"""集成测试

需要真实的外部服务（Prometheus、PostgreSQL、Redis 等）。

运行方式：
    pytest tests/integration/ -v -m integration

标记集成测试：
    @pytest.mark.integration
"""
