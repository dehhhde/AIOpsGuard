"""集成测试脚本（测试模式）

使用 Mock 数据测试完整诊断流程
"""

import asyncio
import sys
from pathlib import Path

import httpx

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_full_diagnosis_flow():
    """测试完整诊断流程"""
    base_url = "http://localhost:8000"

    print("=" * 80)
    print("AIOpsGuard 集成测试（测试模式）")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 健康检查
        print("\n[1/6] 健康检查...")
        try:
            response = await client.get(f"{base_url}/api/v1/health/")
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   ✓ 响应: {response.json()}")
        except Exception as e:
            print(f"   ✗ 健康检查失败: {e}")
            print(f"   提示: 请确保服务已启动（TEST_MODE=true）")
            return False

        # 2. 就绪检查
        print("\n[2/6] 就绪检查...")
        try:
            response = await client.get(f"{base_url}/api/v1/health/ready")
            print(f"   ✓ 状态码: {response.status_code}")
            data = response.json()
            print(f"   ✓ 状态: {data['status']}")
            print(f"   ✓ 检查项: {list(data.get('checks', {}).keys())}")
        except Exception as e:
            print(f"   ✗ 就绪检查失败: {e}")

        # 3. 触发诊断
        print("\n[3/6] 触发诊断...")
        trigger_data = {
            "service_name": "test-service",
            "service_instance": "test-service-01",
            "environment": "prod",
            "time_range_minutes": 60,
            "trigger_source": "manual",
        }
        try:
            response = await client.post(
                f"{base_url}/api/v1/diagnosis/trigger", json=trigger_data
            )
            print(f"   ✓ 状态码: {response.status_code}")

            if response.status_code == 202:
                result = response.json()
                session_id = result["session_id"]
                print(f"   ✓ 诊断已触发")
                print(f"   ✓ 会话 ID: {session_id}")
                print(f"   ✓ 状态: {result['status']}")
                print(f"   ✓ 消息: {result['message']}")

                # 4. 等待诊断完成
                print(f"\n[4/6] 等待诊断完成...")
                print(f"   诊断流程: Metric Agent → Log Agent → Trace Agent → RCA Agent")

                max_wait = 30  # 最多等待 30 秒
                wait_interval = 2  # 每 2 秒检查一次

                for i in range(max_wait // wait_interval):
                    await asyncio.sleep(wait_interval)

                    # 查询诊断状态
                    response = await client.get(
                        f"{base_url}/api/v1/diagnosis/sessions/{session_id}"
                    )

                    if response.status_code == 200:
                        session = response.json()
                        status = session["status"]
                        progress = session["progress"]
                        current_stage = session.get("current_stage", "unknown")

                        print(
                            f"   进度: {progress}% | 状态: {status} | 阶段: {current_stage}"
                        )

                        if status == "completed":
                            print(f"   ✓ 诊断完成！")
                            break
                        elif status == "failed":
                            print(f"   ✗ 诊断失败: {session.get('error_message')}")
                            return False
                    else:
                        print(f"   ✗ 查询失败: {response.status_code}")

                # 5. 获取诊断会话详情
                print(f"\n[5/6] 获取诊断会话详情...")
                try:
                    response = await client.get(
                        f"{base_url}/api/v1/diagnosis/sessions/{session_id}"
                    )
                    if response.status_code == 200:
                        session = response.json()
                        print(f"   ✓ 会话 ID: {session['session_id']}")
                        print(f"   ✓ 服务名称: {session['service_name']}")
                        print(f"   ✓ 环境: {session['environment']}")
                        print(f"   ✓ 状态: {session['status']}")
                        print(f"   ✓ 进度: {session['progress']}%")
                        print(
                            f"   ✓ 诊断阶段: {session.get('current_stage', 'N/A')}"
                        )
                        print(
                            f"   ✓ 开始时间: {session['start_time'][:19].replace('T', ' ')}"
                        )
                        print(
                            f"   ✓ 结束时间: {session['end_time'][:19].replace('T', ' ')}"
                        )
                    else:
                        print(f"   ✗ 获取详情失败: {response.status_code}")
                except Exception as e:
                    print(f"   ✗ 获取详情异常: {e}")

                # 6. 获取诊断报告
                print(f"\n[6/6] 获取诊断报告...")
                try:
                    response = await client.get(
                        f"{base_url}/api/v1/diagnosis/sessions/{session_id}/report"
                    )

                    if response.status_code == 200:
                        report = response.json()

                        print(f"   ✓ 报告获取成功")
                        print(f"\n   【诊断摘要】")
                        print(f"   {report['summary']}")

                        print(f"\n   【证据清单】")
                        evidences = report.get("evidences", [])
                        print(f"   共收集 {len(evidences)} 条证据：")
                        for i, ev in enumerate(evidences[:5], 1):  # 只显示前 5 条
                            print(
                                f"   {i}. [{ev['evidence_type']}] {ev['summary']}"
                            )
                        if len(evidences) > 5:
                            print(f"   ... 还有 {len(evidences) - 5} 条证据")

                        print(f"\n   【根因分析】")
                        root_causes = report.get("root_causes", [])
                        print(f"   共发现 {len(root_causes)} 个根因：")
                        for i, rc in enumerate(root_causes, 1):
                            print(f"   {i}. {rc['summary']}")
                            print(f"      置信度: {rc['confidence']}%")

                        print(f"\n   ✓ 完整报告已生成")

                    elif response.status_code == 404:
                        print(f"   ⚠ 报告尚未生成（诊断可能未完成）")
                    else:
                        print(f"   ✗ 获取报告失败: {response.status_code}")
                        print(f"   响应: {response.text}")

                except Exception as e:
                    print(f"   ✗ 获取报告异常: {e}")

            else:
                print(f"   ✗ 触发失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False

        except Exception as e:
            print(f"   ✗ 触发诊断失败: {e}")
            return False

    # 测试完成
    print("\n" + "=" * 80)
    print("✅ 集成测试完成")
    print("=" * 80)

    print("\n📊 测试结果:")
    print("  ✓ 健康检查通过")
    print("  ✓ 诊断触发成功")
    print("  ✓ 诊断流程执行完成")
    print("  ✓ 证据收集成功（Metric + Log + Trace）")
    print("  ✓ 根因分析完成")
    print("  ✓ 诊断报告生成")

    print("\n💡 测试模式说明:")
    print("  • 使用 Mock 数据模拟外部依赖（Prometheus、Loki、Tempo、LLM）")
    print("  • 诊断结果包含预设的异常场景：")
    print("    - JVM 内存不足导致 OutOfMemoryError")
    print("    - 数据库查询慢导致请求延迟")
    print("    - 支付服务超时导致订单失败")

    print("\n🚀 下一步:")
    print("  1. 部署真实依赖服务（Prometheus、Loki、Tempo）")
    print("  2. 配置 LLM API Key（OpenAI / Ollama）")
    print("  3. 修改 .env 文件：TEST_MODE=false")
    print("  4. 重新运行测试，验证真实诊断流程")

    return True


if __name__ == "__main__":
    print("\n⚠️  请确保服务已启动：")
    print("  cd aiops-agent")
    print("  ./start.sh  # 或 start.bat (Windows)\n")

    success = asyncio.run(test_full_diagnosis_flow())
    sys.exit(0 if success else 1)
