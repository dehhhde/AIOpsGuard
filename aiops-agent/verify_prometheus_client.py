#!/usr/bin/env python
"""验证 Prometheus 客户端功能"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_prometheus_client():
    """测试 Prometheus 客户端"""
    from infrastructure.external.prometheus_client import PrometheusClient
    
    print("=" * 60)
    print("Prometheus 客户端验证")
    print("=" * 60)
    print()
    
    try:
        # 1. 初始化测试
        print("1. 初始化客户端...")
        client = PrometheusClient(
            base_url="http://localhost:9090",
            timeout=5.0
        )
        print(f"   ✓ 客户端创建成功")
        print(f"   - Base URL: {client.base_url}")
        print(f"   - Timeout: {client.timeout}s")
        print()
        
        # 2. 健康检查测试
        print("2. 健康检查...")
        async with client:
            health = await client.health()
            if health["is_healthy"]:
                print(f"   ✓ Prometheus 健康状态: OK")
            else:
                print(f"   ✗ Prometheus 不可用")
                print(f"   提示: 请确保 Prometheus 运行在 http://localhost:9090")
                return False
        print()
        
        # 3. 即时查询测试
        print("3. 即时查询测试...")
        async with client:
            result = await client.query("up")
            if result["status"] == "success":
                result_count = len(result["data"]["result"])
                print(f"   ✓ 查询成功")
                print(f"   - 结果类型: {result['data']['resultType']}")
                print(f"   - 结果数量: {result_count}")
                
                if result_count > 0:
                    sample = result["data"]["result"][0]
                    print(f"   - 示例指标: {sample['metric'].get('__name__', 'N/A')}")
            else:
                print(f"   ✗ 查询失败: {result.get('error', 'Unknown error')}")
                return False
        print()
        
        # 4. 范围查询测试
        print("4. 范围查询测试...")
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=5)
        
        async with client:
            result = await client.query_range(
                query="up",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                step="15s"
            )
            if result["status"] == "success":
                result_count = len(result["data"]["result"])
                print(f"   ✓ 范围查询成功")
                print(f"   - 时间范围: 最近 5 分钟")
                print(f"   - 步长: 15s")
                print(f"   - 结果数量: {result_count}")
            else:
                print(f"   ✗ 范围查询失败")
                return False
        print()
        
        # 5. 标签查询测试
        print("5. 标签查询测试...")
        async with client:
            result = await client.labels()
            if result["status"] == "success":
                labels = result["data"]
                print(f"   ✓ 标签查询成功")
                print(f"   - 标签数量: {len(labels)}")
                print(f"   - 示例标签: {', '.join(labels[:5])}")
            else:
                print(f"   ✗ 标签查询失败")
                return False
        print()
        
        # 6. 序列查询测试
        print("6. 序列查询测试...")
        async with client:
            result = await client.series(
                match=["up"],
                start=start_time.isoformat()
            )
            if result["status"] == "success":
                series_count = len(result["data"])
                print(f"   ✓ 序列查询成功")
                print(f"   - 序列数量: {series_count}")
                if series_count > 0:
                    sample = result["data"][0]
                    print(f"   - 示例序列: {sample}")
            else:
                print(f"   ✗ 序列查询失败")
                return False
        print()
        
        # 成功
        print("=" * 60)
        print("✓ 所有测试通过！Prometheus 客户端工作正常。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n")
    success = await test_prometheus_client()
    print()
    
    if success:
        return 0
    else:
        print("提示：")
        print("1. 确保 Prometheus 正在运行：")
        print("   docker run -d -p 9090:9090 prom/prometheus")
        print()
        print("2. 或修改配置文件中的 PROMETHEUS_URL")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
