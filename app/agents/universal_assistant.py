"""
Confluence 通用问答助手 (Universal Q&A Assistant)

功能:
- 利用 deepagents 的智能任务分解能力
- 支持各种复杂度的问题
- 自动规划查询策略和并发处理
- 输出 Markdown 格式答案含来源引用
"""

import asyncio

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from structlog.stdlib import get_logger

from app.agents.confluence_agent import (
    get_confluence_tools,
    reset_mcp_tools_cache,
)
from app.core.config import settings

logger = get_logger(__name__)


# ============================================================================
# 通用问答系统提示词
# ============================================================================

universal_qa_instructions = """你是 Confluence 知识库的通用问答助手。

任务: 根据用户问题，快速准确地从知识库检索和综合相关信息，给出结构化答案。

你应该:

1. 分析问题: 识别问题类型和复杂度
   - 简单问题 -> 精准搜索 + 获取 1-2 个页面
   - 复杂问题 -> 多个搜索查询 + 并发获取多个页面
   - 跨域问题 -> 识别多个知识域，逐一检索

2. 智能规划: 使用任务工具规划最优执行策略
   - 利用 write_todos 工具分解任务
   - 识别哪些任务可以并发执行
   - 避免重复的搜索查询（同一内容只搜索一次）
   - 确保在 20 秒内完成

3. 执行检索: 并发执行搜索和获取操作
   - 使用 confluence_search 找到相关文档
   - 使用 get_confluence_page 获取完整内容
   - 每个搜索查询只执行一次，不要重复搜索相同内容

4. 生成答案: 综合信息，输出 Markdown 格式
   - 清晰的问题总结
   - 分小节的答案内容
   - 每个信息源附加来源链接
   - 最后列出所有参考资源

## 输出格式 (Markdown)

使用以下格式组织答案:

```markdown
# [问题概括]

## 答案

[主要内容，根据问题复杂度分小节]

## 参考资源

- [页面标题](https://confluence-url/pages/...)
```

## 重要约束

- 所有信息必须来自 Confluence，不要编造或猜测
- 响应时间必须在 20 秒内
- 避免重复的工具调用，同一搜索查询只执行一次
- 如果没有找到相关信息，明确告知用户
- 在答案中明确标注信息来源"""


# ============================================================================
# Agent 工厂函数
# ============================================================================


async def _create_universal_qa_agent_async():
    """
    异步创建 Confluence 通用问答助手。
    """
    llm = init_chat_model(model=settings.INIT_LLM_MODEL)
    tools = await get_confluence_tools()

    return create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=universal_qa_instructions,
    )


def _create_universal_qa_agent_impl():
    """
    创建 Confluence 通用问答助手的同步包装。
    """
    return asyncio.run(_create_universal_qa_agent_async())


# ============================================================================
# 全局 Agent 实例和调用接口
# ============================================================================

universal_qa_agent = _create_universal_qa_agent_impl()


# ============================================================================
# 工具重置接口 (调试用)
# ============================================================================


async def reset_cache():
    """
    重置 MCP 工具缓存。

    用于在 Confluence 配置更新后重新初始化工具。
    """
    await reset_mcp_tools_cache()
    logger.info("mcp_tools_cache_reset")
