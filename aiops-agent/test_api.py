"""API 测试脚本"""

import asyncio
import httpx


async def test_api():
    """测试 API 端点"""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # 1. 健康检查
        print("\n[1/5] 测试健康检查...")
        response = await client.get(f"{base_url}/api/v1/health/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")

        # 2. 就绪检查
        print("\n[2/5] 测试就绪检查...")
        response = await client.get(f"{base_url}/api/v1/health/ready")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")

        # 3. 触发诊断
        print("\n[3/5] 测试触发诊断...")
        trigger_data = {
            "service_name": "test-service",
            "environment": "prod",
            "time_range_minutes": 60,
            "trigger_source": "manual",
        }
        response = await client.post(
            f"{base_url}/api/v1/diagnosis/trigger", json=trigger_data
        )
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {result}")

        if response.status_code == 202:
            session_id = result["session_id"]

            # 4. 查询诊断会话
            print(f"\n[4/5] 测试查询诊断会话（session_id: {session_id}）...")
            response = await client.get(
                f"{base_url}/api/v1/diagnosis/sessions/{session_id}"
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")

            # 等待一会儿让诊断执行
            print("\n   等待 5 秒让诊断执行...")
            await asyncio.sleep(5)

            # 5. 获取诊断报告
            print(f"\n[5/5] 测试获取诊断报告（session_id: {session_id}）...")
            response = await client.get(
                f"{base_url}/api/v1/diagnosis/sessions/{session_id}/report"
            )
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                report = response.json()
                print(f"   诊断状态: {report['session']['status']}")
                print(f"   证据数量: {len(report['evidences'])}")
                print(f"   根因数量: {len(report['root_causes'])}")
            else:
                print(f"   响应: {response.json()}")

    print("\n✅ API 测试完成")


if __name__ == "__main__":
    asyncio.run(test_api())
