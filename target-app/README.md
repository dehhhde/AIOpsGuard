# Target Application - AIOps 被测应用

## 项目介绍

这是一个故意植入各类生产环境典型问题的 Spring Boot 应用，作为 AIOps 诊断系统的"故障靶场"。

## 功能特性

### 问题接口

| 接口路径 | 问题类型 | 描述 |
|---------|---------|------|
| `/api/leak/memory` | 内存泄漏 | 每次请求分配 10MB 内存并保留 |
| `/api/leak/thread` | 线程泄漏 | 创建线程但不释放 |
| `/api/slow/sql` | 慢 SQL | 执行复杂的数据库查询 |
| `/api/pool/exhaust` | 连接池耗尽 | 借出数据库连接但不归还 |
| `/api/cpu/spike` | CPU 飙高 | 启动 CPU 密集型计算 |
| `/api/deadlock` | 死锁 | 两个线程互相等待锁 |
| `/api/normal` | 正常接口 | 无问题，用于基线对比 |

### 管理接口

| 接口路径 | 方法 | 描述 |
|---------|------|------|
| `/api/admin/problems/switches` | GET | 获取所有问题开关状态 |
| `/api/admin/problems/switches/{type}/enable` | POST | 启用指定问题 |
| `/api/admin/problems/switches/{type}/disable` | POST | 禁用指定问题 |
| `/actuator/health` | GET | 健康检查 |
| `/actuator/metrics` | GET | 指标端点 |
| `/actuator/prometheus` | GET | Prometheus 格式指标 |

## 快速开始

### 前置要求

- JDK 21
- Maven 3.9+

### 本地运行

```bash
# 1. 编译项目
mvn clean package

# 2. 运行应用
java -jar target/target-app-1.0.0.jar

# 3. 访问应用
curl http://localhost:8080/api/normal
```

### 配置问题开关

编辑 `application.yml`:

```yaml
problem:
  switches:
    MEMORY_LEAK: true    # 启用内存泄漏
    THREAD_LEAK: false
    SLOW_SQL: true       # 启用慢 SQL
    POOL_EXHAUST: false
    CPU_SPIKE: false
    DEADLOCK: false
```

或通过 API 动态控制:

```bash
# 启用内存泄漏
curl -X POST http://localhost:8080/api/admin/problems/switches/MEMORY_LEAK/enable

# 禁用内存泄漏
curl -X POST http://localhost:8080/api/admin/problems/switches/MEMORY_LEAK/disable

# 查看所有开关状态
curl http://localhost:8080/api/admin/problems/switches
```

## 测试场景

### 1. 内存泄漏测试

```bash
# 启用内存泄漏
curl -X POST http://localhost:8080/api/admin/problems/switches/MEMORY_LEAK/enable

# 连续调用 50 次，分配 500MB 内存
for i in {1..50}; do
  curl http://localhost:8080/api/leak/memory
  echo "Request $i completed"
  sleep 1
done

# 查看内存状态
curl http://localhost:8080/api/leak/memory/status

# 重置缓存
curl -X POST http://localhost:8080/api/leak/memory/reset
```

### 2. 线程泄漏测试

```bash
# 启用线程泄漏
curl -X POST http://localhost:8080/api/admin/problems/switches/THREAD_LEAK/enable

# 创建 100 个泄漏线程
for i in {1..100}; do
  curl http://localhost:8080/api/leak/thread
  echo "Leaked $i threads"
done

# 查看线程状态
curl http://localhost:8080/api/leak/thread/status
```

### 3. 慢 SQL 测试

```bash
# 启用慢 SQL
curl -X POST http://localhost:8080/api/admin/problems/switches/SLOW_SQL/enable

# 执行慢查询
curl http://localhost:8080/api/slow/sql
```

### 4. CPU 飙高测试

```bash
# 启用 CPU 飙高
curl -X POST http://localhost:8080/api/admin/problems/switches/CPU_SPIKE/enable

# 触发 CPU 飙高（持续 30 秒）
curl http://localhost:8080/api/cpu/spike?durationSeconds=30
```

### 5. 死锁测试

```bash
# 启用死锁
curl -X POST http://localhost:8080/api/admin/problems/switches/DEADLOCK/enable

# 触发死锁
curl http://localhost:8080/api/deadlock
```

## 可观测性

### Prometheus 指标

访问 `http://localhost:8080/actuator/prometheus` 查看所有指标。

关键指标：
- `jvm_memory_used_bytes` - JVM 内存使用量
- `jvm_threads_live` - 活跃线程数
- `process_cpu_usage` - 进程 CPU 使用率
- `http_server_requests_seconds` - HTTP 请求指标
- `hikaricp_connections_active` - 数据库连接池活跃连接数

### 健康检查

```bash
curl http://localhost:8080/actuator/health
```

响应示例：
```json
{
  "status": "DOWN",
  "components": {
    "problemHealth": {
      "status": "DOWN",
      "details": {
        "problems": {
          "MEMORY_LEAK": true,
          "THREAD_LEAK": true
        },
        "message": "Multiple critical problems active"
      }
    }
  }
}
```

## Docker 部署

```bash
# 构建镜像
docker build -t target-app:1.0.0 .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=docker \
  --name target-app \
  target-app:1.0.0
```

## 注意事项

⚠️ **警告**：此应用仅用于测试环境，绝对不能部署到生产环境！

1. **资源限制**：建议在 Docker 中运行时设置内存限制（如 `-m 2g`）
2. **问题控制**：所有问题都可通过开关控制，避免失控
3. **定期重置**：测试完成后记得重置缓存和释放资源
4. **监控告警**：建议配合 Prometheus + Grafana 监控指标变化

## 技术栈

- Spring Boot 3.2.0
- JDK 21
- H2 Database
- Micrometer (Prometheus)
- OpenTelemetry (可选)
- Lombok

## 开发计划

- [x] P0: 基础框架 + 内存泄漏 + 慢 SQL
- [x] P1: 线程泄漏 + 连接池耗尽 + CPU 飙高 + 死锁
- [x] P2: 可观测性集成（Micrometer + OpenTelemetry）
- [x] P3: 健康检查 + 管理接口
- [ ] P4: 更多问题场景（网络超时、依赖服务异常等）

## License

MIT License
