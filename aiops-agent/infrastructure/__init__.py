"""基础设施层

本层负责与外部系统交互，实现技术细节。

模块：
- external: 外部服务客户端（Prometheus、Loki、Tempo等）
- persistence: 持久化（数据库、ORM、仓储实现）
- cache: 缓存（Redis）
- messaging: 消息队列（Kafka）
- monitoring: 监控埋点
"""
