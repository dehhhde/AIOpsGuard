"""LLM 客户端"""

from typing import Any, AsyncIterator, Dict, List, Optional

import structlog
from openai import AsyncOpenAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = structlog.get_logger(__name__)


class LLMClientError(Exception):
    """LLM 客户端错误"""

    pass


class LLMClient:
    """LLM 客户端

    支持：
    - OpenAI API（gpt-4, gpt-3.5-turbo）
    - Ollama 本地模型（兼容 OpenAI API）
    - 流式输出
    - 重试机制
    - 超时控制
    """

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.enabled = settings.llm_enabled
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    async def connect(self) -> None:
        """连接 LLM 服务"""
        if not self.enabled:
            logger.info("llm_disabled_skip_connect")
            return

        try:
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout,
            )
            logger.info(
                "llm_connected",
                model=self.model,
                base_url=settings.llm_base_url,
            )
        except Exception as e:
            logger.error("llm_connect_failed", error=str(e))
            raise LLMClientError(f"Failed to connect to LLM: {e}")

    async def close(self) -> None:
        """关闭连接"""
        if self.client:
            await self.client.close()
            logger.info("llm_closed")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """聊天补全（非流式）

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度（可选，默认使用配置）
            max_tokens: 最大 token 数（可选）

        Returns:
            LLM 响应内容

        Raises:
            LLMClientError: LLM 调用失败
        """
        from config.settings import settings as app_settings

        # 测试模式：返回 Mock 数据
        if app_settings.test_mode:
            logger.info("test_mode_mock_llm_response")
            return self._generate_mock_response(messages)

        if not self.enabled or not self.client:
            logger.warning("llm_disabled_return_placeholder")
            return "[LLM disabled] This is a placeholder response."

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type(Exception),
            ):
                with attempt:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature or self.temperature,
                        max_tokens=max_tokens or self.max_tokens,
                    )

                    content = response.choices[0].message.content

                    logger.info(
                        "llm_chat_completed",
                        model=self.model,
                        input_tokens=response.usage.prompt_tokens if response.usage else 0,
                        output_tokens=response.usage.completion_tokens
                        if response.usage
                        else 0,
                    )

                    return content or ""

        except Exception as e:
            logger.error("llm_chat_failed", error=str(e), messages=messages)
            raise LLMClientError(f"LLM chat failed: {e}")

    def _generate_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """生成 Mock LLM 响应（测试模式）"""
        import json

        from infrastructure.external.mock_data import MockDataGenerator

        mock_gen = MockDataGenerator()

        # 根据 system message 判断是哪个 Agent
        system_content = messages[0].get("content", "") if messages else ""
        user_content = messages[1].get("content", "") if len(messages) > 1 else ""

        if "指标分析" in system_content or "Metric" in system_content:
            # Metric Agent
            result = mock_gen.generate_llm_metric_analysis("test-service", "")
        elif "日志分析" in system_content or "Log" in system_content:
            # Log Agent
            result = mock_gen.generate_llm_log_analysis("test-service", "")
        elif "链路追踪" in system_content or "Trace" in system_content:
            # Trace Agent
            result = mock_gen.generate_llm_trace_analysis("test-service", "")
        elif "根因分析" in system_content or "RCA" in system_content:
            # RCA Agent
            result = mock_gen.generate_llm_rca_analysis("test-service", "")
        else:
            # 默认响应
            result = {"message": "Mock LLM response", "data": []}

        return json.dumps(result, ensure_ascii=False, indent=2)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """聊天补全（流式输出）

        Args:
            messages: 消息列表
            temperature: 温度

        Yields:
            LLM 响应片段
        """
        if not self.enabled or not self.client:
            logger.warning("llm_disabled_stream_skipped")
            yield "[LLM disabled]"
            return

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("llm_stream_failed", error=str(e))
            raise LLMClientError(f"LLM stream failed: {e}")

    async def health(self) -> bool:
        """健康检查"""
        if not self.enabled or not self.client:
            return False

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.warning("llm_health_check_failed", error=str(e))
            return False
