"""
LangGraph 应用启动入口

在 langgraph-cli 启动时执行一次初始化，所有 Agent 调用共享同一个日志和 MCP 实例。
这样可以避免重复初始化导致的日志重复输出和 MCP 服务器多次启动。

使用方式：
    langgraph.json 中配置：
    {
      "graphs": {
        "universal_qa": "./main.py:universal_qa_agent"
      }
    }
"""

from app.agents.confluence_agent import initialize_mcp_tools_on_import
from app.core.log_adapter import setup_logging

# ============================================================================
# 启动时全局初始化 - 仅执行一次
# ============================================================================

# 初始化日志系统（仅在模块导入时调用一次，后续调用会被守卫拦截）
setup_logging()

# 🔥 在模块导入时自动触发
initialize_mcp_tools_on_import()

# ============================================================================
# 导出 Agent 供 LangGraph 使用
# ============================================================================

from app.agents.confluence_agent import create_confluence_research_agent_async  # noqa: E402
from app.agents.universal_assistant import create_universal_qa_agent_async  # noqa: E402

__all__ = ["create_universal_qa_agent_async", "create_confluence_research_agent_async"]
