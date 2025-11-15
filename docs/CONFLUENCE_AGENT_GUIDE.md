# Confluence Agent 使用指南

## 目录

1. [概览](#概览)
2. [快速开始](#快速开始)
3. [核心功能](#核心功能)
4. [架构设计](#架构设计)
5. [API 参考](#api-参考)
6. [使用示例](#使用示例)
7. [配置指南](#配置指南)
8. [故障排查](#故障排查)
9. [最佳实践](#最佳实践)

---

## 概览

Confluence Agent 是一个基于 **deepagents** 框架和 **MCP（Model Context Protocol）** 协议构建的智能研究助手系统。它能够从 Atlassian Confluence 企业知识库中自动提取、分析和综合信息，为用户生成深度研究报告和快速问答。

### 核心优势

- **智能分解**：自动分析问题复杂度，规划最优搜索策略
- **多层代理**：支持研究 + 评审的多轮迭代工作流
- **来源追踪**：自动收集和标注 Confluence 页面引用
- **高效缓存**：全局 MCP 客户端和工具缓存，避免重复初始化
- **灵活部署**：支持同步和异步调用，适配多种集成场景

### 主要用途

- **深度研究**：进行多轮搜索和质量评审，生成专业报告
- **快速问答**：快速从知识库检索信息，回答员工日常问题
- **知识挖掘**：自动索引和综合跨越多个 Confluence 页面的信息

---

## 快速开始

### 1. 环境准备

确保项目依赖已安装：

```bash
uv sync  # 使用 uv 包管理器
```

### 2. 配置 MCP 服务器

在项目根目录创建 `.mcp.json` 文件，配置 MCP 服务器（Claude Code IDE 格式）：

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "python",
      "args": ["-m", "mcp_atlassian_server"],
      "env": {
        "CONFLUENCE_URL": "https://your-confluence.atlassian.net",
        "CONFLUENCE_TOKEN": "your-api-token"
      }
    }
  }
}
```

### 3. 启动应用

使用 LangGraph CLI 启动应用：

```bash
langgraph up --host 0.0.0.0 --port 8000
```

或者在 Python 代码中直接使用：

```python
from app.agents.confluence_agent import confluence_agent

# 使用 Research Agent（深度研究）
result = confluence_agent.invoke({
    "messages": [{"role": "user", "content": "请研究公司的数据隐私政策"}]
})
print(result)
```

### 4. 验证安装

访问 http://localhost:8000 查看 LangGraph 仪表盘，或在 Python 中：

```python
from app.agents.confluence_agent import get_mcp_tools

import asyncio
tools = asyncio.run(get_mcp_tools())
print(f"已加载 {len(tools)} 个工具")
```

---

## 核心功能

### 1. Confluence Research Agent（研究代理）

专业的深度研究助手，适合需要高质量输出的场景。

#### 工作流

```
┌─ 用户提问
│
├─ 写入 question.txt（记录原始提问）
│
├─ 调用 Research Sub-Agent
│  ├─ confluence_search（搜索相关文档）
│  ├─ confluence_get_page（获取完整内容）
│  └─ confluence_get_comments（获取讨论内容）
│
├─ 综合信息生成 final_report.md
│
├─ 调用 Critique Sub-Agent（可选）
│  └─ confluence_search（验证事实）
│
├─ 根据反馈修改报告（可选）
│
└─ 返回最终报告
```

#### 特点

- **多轮迭代**：支持自动评审 → 修改 → 再次评审
- **结构化输出**：生成专业的 Markdown 格式报告
- **智能引用**：自动追踪和标注所有 Confluence 页面源
- **灵活报告格式**：支持对比、列表、总结等多种结构

#### 系统提示词

Research Agent 遵循以下约束：

```
1. 首先写入 question.txt 记录用户提问
2. 使用 confluence-research-agent 进行深度搜索
3. 当信息充分时，生成 final_report.md
4. 可选：调用 confluence-critique-agent 进行质量评审
5. 根据反馈迭代修改报告（单次修改）
6. 报告必须使用与用户相同的语言
7. 包含完整的来源引用和链接
```

### 2. Universal QA Agent（通用问答助手）

快速问答助手，针对简单和中等复杂度的问题优化。

#### 工作流

```
┌─ 用户提问
│
├─ 分析问题复杂度
│
├─ 并发执行搜索
│  ├─ confluence_search（多个搜索查询）
│  └─ confluence_get_page（获取相关页面）
│
├─ 综合信息
│
└─ 返回 Markdown 格式答案（含来源）
```

#### 特点

- **快速响应**：20 秒内完成回答
- **智能规划**：自动识别并发机会
- **避免重复**：同一搜索查询仅执行一次
- **清晰结构**：问题总结、分小节答案、参考资源

#### 适用场景

- 员工快速咨询
- 知识库常见问题
- 日常信息查找

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│         LangGraph 应用层                  │
│   (main.py - 启动和全局初始化)            │
└────────┬────────────────────────────────┘
         │
         ├─ setup_logging()          [日志初始化]
         ├─ initialize_mcp_tools_sync() [同步 MCP 初始化]
         │
         ↓
┌─────────────────────────────────────────┐
│       Agent 工厂层                        │
│  (confluence_agent.py, universal_assistant.py) │
└────────┬────────────────────────────────┘
         │
         ├─ create_confluence_research_agent()
         │  └─ create_deep_agent()
         │     ├─ system_prompt
         │     ├─ tools
         │     ├─ subagents [research, critique]
         │     └─ backend (FilesystemBackend)
         │
         └─ create_universal_qa_agent()
            └─ create_deep_agent()
               ├─ system_prompt
               ├─ tools
               └─ backend (FilesystemBackend)
         │
         ↓
┌─────────────────────────────────────────┐
│      MCP 工具集成层                       │
│   (confluence_agent.py - MCP 客户端管理) │
└────────┬────────────────────────────────┘
         │
         ├─ get_mcp_client()      [全局单例 MCP 客户端]
         ├─ get_mcp_tools()       [工具字典缓存]
         └─ reset_mcp_tools_cache() [缓存重置]
         │
         ↓
┌─────────────────────────────────────────┐
│       MCP 服务器                          │
│   (通过 .mcp.json 配置连接)               │
│   - confluence_search                   │
│   - confluence_get_page                 │
│   - confluence_get_comments             │
└─────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│     Atlassian Confluence 知识库            │
│   (企业内部文档、页面、评论)                 │
└─────────────────────────────────────────┘
```

### 关键设计模式

#### 全局单例 + 延迟初始化

```python
_mcp_client: MultiServerMCPClient | None = None

async def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client
    if _mcp_client is None:
        # 仅第一次初始化
        _mcp_client = MultiServerMCPClient(...)
    return _mcp_client
```

**优势**：
- ✓ 避免重复初始化开销
- ✓ 共享同一客户端实例，减少内存占用
- ✓ 支持热重载（通过 reset_mcp_tools_cache）

#### 工具缓存策略

```python
_mcp_tools_cache: dict[str, dict] | None = None

async def get_mcp_tools() -> dict[str, dict]:
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        _mcp_tools_cache = await _fetch_all_mcp_tools()
    return _mcp_tools_cache
```

**优势**：
- ✓ 减少 MCP 服务器调用
- ✓ 加快工具获取速度
- ✓ 支持缓存无效化

#### 子代理分工设计

```python
subagents=[
    {
        "name": "confluence-research-agent",
        "system_prompt": sub_research_prompt,
        "tools": confluence_tools,
    },
    {
        "name": "confluence-critique-agent",
        "system_prompt": sub_critique_prompt,
        "tools": [search_tool],  # 仅搜索工具
    },
]
```

**职责划分**：
- **Research Agent**：执行搜索、提取信息
- **Critique Agent**：评审报告、验证事实、建议改进
- **Main Agent**：协调子代理、管理工作流、生成最终输出

### 配置和初始化流程

```
应用启动 (main.py)
    ↓
setup_logging()
    ├─ 初始化 structlog 日志系统
    └─ 设置日志级别和输出格式
    ↓
initialize_mcp_tools_sync()
    ├─ asyncio.run() 进入异步上下文
    └─ await get_mcp_tools()
        ├─ await get_mcp_client()
        │  ├─ 加载 .mcp.json
        │  ├─ 转换配置格式
        │  └─ 创建 MultiServerMCPClient
        │
        └─ 获取所有可用工具
           └─ 构建 {tool_name: tool_object} 字典
    ↓
应用就绪
```

---

## API 参考

### MCP 工具管理

#### `async get_mcp_client() → MultiServerMCPClient`

获取或创建全局 MCP 客户端实例。

**返回值**：
- 初始化完成的 `MultiServerMCPClient` 实例

**异常**：
- `FileNotFoundError`：.mcp.json 不存在
- `ValueError`：配置格式无效或未找到 MCP 服务器

**示例**：
```python
import asyncio
from app.agents.confluence_agent import get_mcp_client

client = asyncio.run(get_mcp_client())
print(client)
```

#### `async get_mcp_tools() → dict[str, dict]`

获取缓存的 MCP 工具字典。

**返回值**：
- `{tool_name: tool_object}` 字典

**异常**：
- `ValueError`：初始化失败或找不到工具

**示例**：
```python
import asyncio
from app.agents.confluence_agent import get_mcp_tools

tools = asyncio.run(get_mcp_tools())
for tool_name, tool_obj in tools.items():
    print(f"{tool_name}: {tool_obj.description}")
```

#### `async reset_mcp_tools_cache() → None`

重置 MCP 工具缓存。

**说明**：下一次调用 `get_mcp_tools()` 时会自动重新加载。

**示例**：
```python
import asyncio
from app.agents.confluence_agent import reset_mcp_tools_cache

await reset_mcp_tools_cache()
print("缓存已重置，下次自动重新加载")
```

### Agent 创建

#### `create_confluence_research_agent() → Agent`

创建 Confluence 研究代理（同步包装）。

**返回值**：
- 配置完整的 `create_deep_agent` 实例

**示例**：
```python
from app.agents.confluence_agent import confluence_agent

result = confluence_agent.invoke({
    "messages": [{"role": "user", "content": "请研究..."}]
})
```

#### `create_universal_qa_agent() → Agent`

创建通用问答代理（同步包装）。

**返回值**：
- 配置完整的 `create_deep_agent` 实例

**示例**：
```python
from app.agents.universal_assistant import universal_qa_agent

result = universal_qa_agent.invoke({
    "messages": [{"role": "user", "content": "什么是...？"}]
})
```

---

## 使用示例

### 示例 1：使用 Research Agent 进行深度研究

```python
from app.agents.confluence_agent import confluence_agent

# 提问
user_question = "请详细研究公司的云架构和数据安全措施"

result = confluence_agent.invoke({
    "messages": [
        {"role": "user", "content": user_question}
    ]
})

# 查看最终报告
import os
with open("./output/final_report.md", "r") as f:
    print(f.read())
```

### 示例 2：使用 Universal QA 进行快速问答

```python
from app.agents.universal_assistant import universal_qa_agent

# 快速提问
result = universal_qa_agent.invoke({
    "messages": [
        {"role": "user", "content": "如何向 IT 部门申请新的软件许可证？"}
    ]
})

# 获取答案
print(result["messages"][-1]["content"])
```

### 示例 3：并发调用多个 Agent

```python
import asyncio
from app.agents.confluence_agent import confluence_agent
from app.agents.universal_assistant import universal_qa_agent

async def parallel_research():
    # 同时执行两个研究任务
    questions = [
        "研究数据治理政策",
        "总结云迁移计划"
    ]
    
    tasks = [
        asyncio.to_thread(
            confluence_agent.invoke,
            {"messages": [{"role": "user", "content": q}]}
        )
        for q in questions
    ]
    
    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(parallel_research())
```

### 示例 4：处理带有自定义系统提示的 Agent

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from app.agents.confluence_agent import get_confluence_tools
import asyncio

async def create_custom_agent():
    # 自定义系统提示
    custom_prompt = """你是 Confluence 知识库的专业顾问。
    你的任务是从知识库中查找最相关的内容，并以清晰、专业的方式呈现。
    特别关注：
    1. 最新的政策更新
    2. 团队最佳实践
    3. 常见问题的解决方案
    """
    
    llm = init_chat_model(model="openai:gpt-4")
    tools = await get_confluence_tools()
    
    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=custom_prompt,
    )
    
    return agent

# 使用自定义 Agent
custom_agent = asyncio.run(create_custom_agent())
result = custom_agent.invoke({
    "messages": [{"role": "user", "content": "最新的安全政策是什么？"}]
})
```

---

## 配置指南

### 1. MCP 服务器配置 (.mcp.json)

Confluence Agent 通过 `.mcp.json` 配置 MCP 服务器。格式遵循 Claude Code IDE 规范：

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "python",
      "args": ["-m", "mcp_atlassian_server"],
      "env": {
        "CONFLUENCE_URL": "https://your-confluence.atlassian.net",
        "CONFLUENCE_TOKEN": "your-api-token",
        "CONFLUENCE_USER": "user@company.com"
      },
      "cwd": "/path/to/mcp/server",
      "encoding": "utf-8"
    }
  }
}
```

**关键字段**：
- `command`：MCP 服务器启动命令
- `args`：命令参数
- `env`：环境变量（通常包含认证信息）
- `cwd`：工作目录（可选）
- `encoding`：字符编码（默认 utf-8）

### 2. 环境变量配置 (.env)

在 `.env` 文件中配置应用级别的设置：

```env
# LLM 模型配置
INIT_LLM_MODEL=openai:deepseek-ai/DeepSeek-V3.2-Exp
VL_MODEL_NAME=Qwen/Qwen3-VL-32B-Instruct

# 向量和排序模型
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
RERANK_MODEL=Qwen/Qwen3-Reranker-8B

# API 端点
RERANK_BASE_URL=https://api.siliconflow.cn/v1/rerank

# 文件上传目录
UPLOAD_DIR=/app/uploads
```

### 3. 应用配置 (app/core/config.py)

配置类基于 Pydantic 设置，自动从环境变量和 `.env` 文件加载：

```python
from app.core.config import settings

# 访问配置
print(settings.INIT_LLM_MODEL)
print(settings.EMBEDDING_MODEL)
print(settings.RERANK_BASE_URL)
```

### 4. 日志配置

日志通过 `setup_logging()` 初始化，在 `app/core/log_adapter.py` 中定义：

```python
from app.core.log_adapter import setup_logging

# 应用启动时调用一次
setup_logging()

# 获取日志记录器
from structlog.stdlib import get_logger
logger = get_logger(__name__)

logger.info("operation", key="value")
logger.warning("warning_event", reason="...")
logger.error("error_event", error="...")
```

### 5. 输出目录配置

Agent 使用 `FilesystemBackend` 将中间文件存储在 `./output` 目录：

```python
backend=FilesystemBackend(root_dir="./output")
```

确保该目录存在且具有写权限：

```bash
mkdir -p ./output
chmod 755 ./output
```

生成的文件：
- `question.txt`：原始提问
- `final_report.md`：最终报告

---

## 故障排查

### 问题 1：找不到 .mcp.json 文件

**错误信息**：
```
FileNotFoundError: MCP config file not found: .mcp.json
```

**解决方案**：
1. 在项目根目录创建 `.mcp.json`
2. 确保文件路径正确（必须在项目根目录）
3. 检查文件权限（确保可读）

```bash
ls -la .mcp.json
cat .mcp.json  # 验证 JSON 格式
```

### 问题 2：MCP 服务器连接失败

**错误信息**：
```
mcp_client_initialization_failed
```

**解决方案**：
1. 验证 MCP 服务器进程是否运行
2. 检查 `command` 和 `args` 是否正确
3. 验证环境变量（CONFLUENCE_URL, CONFLUENCE_TOKEN）
4. 检查网络连接

```bash
# 测试 Confluence 连接
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-confluence.atlassian.net/wiki/rest/api/space
```

### 问题 3：找不到 Confluence 工具

**错误信息**：
```
no_confluence_tools_found or confluence_tool_not_found
```

**解决方案**：
1. 确认 MCP 服务器提供了正确的工具
2. 检查期望的工具名称：
   - `confluence_search`
   - `confluence_get_page`
   - `confluence_get_comments`

```python
import asyncio
from app.agents.confluence_agent import get_mcp_tools

async def check_tools():
    tools = await get_mcp_tools()
    print("可用工具：")
    for name in tools.keys():
        print(f"  - {name}")

asyncio.run(check_tools())
```

### 问题 4：异步/同步混用导致的事件循环错误

**错误信息**：
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**解决方案**：
1. 不要在异步上下文中使用 `asyncio.run()`
2. 使用 `await` 替代 `asyncio.run()`
3. 或使用 `asyncio.to_thread()` 在线程中执行同步代码

```python
# ❌ 错误：在异步函数中使用 asyncio.run()
async def bad_function():
    result = asyncio.run(get_mcp_tools())  # 错误！

# ✅ 正确：使用 await
async def good_function():
    result = await get_mcp_tools()  # 正确！
```

### 问题 5：文件权限错误

**错误信息**：
```
PermissionError: [Errno 13] Permission denied: './output/final_report.md'
```

**解决方案**：
1. 确保 `./output` 目录存在且可写
2. 检查目录权限

```bash
mkdir -p ./output
chmod 755 ./output
ls -ld ./output
```

### 问题 6：模型配置错误

**错误信息**：
```
Model not found or API key invalid
```

**解决方案**：
1. 检查 INIT_LLM_MODEL 配置
2. 验证 API 密钥（在环境变量中）
3. 检查网络连接

```bash
# 验证配置
grep INIT_LLM_MODEL .env
# 验证 API 密钥是否设置
echo $OPENAI_API_KEY  # 或其他模型的密钥
```

---

## 最佳实践

### 1. 启动时的完整初始化

在应用启动时一次性初始化所有资源，避免首次调用时的延迟：

```python
# main.py
from app.core.log_adapter import setup_logging
from app.agents.confluence_agent import initialize_mcp_tools_sync

# 立即初始化
setup_logging()
initialize_mcp_tools_sync()

# 现在可以导入和使用 Agent
from app.agents.confluence_agent import confluence_agent
from app.agents.universal_assistant import universal_qa_agent
```

### 2. 选择合适的 Agent 类型

- **Research Agent**：需要深度研究、高质量输出、允许更长响应时间
- **Universal QA Agent**：需要快速回答、简洁输出、20 秒内完成

```python
# 根据问题复杂度选择 Agent
if is_complex_research_topic:
    agent = confluence_agent  # Research Agent
else:
    agent = universal_qa_agent  # Universal QA Agent
```

### 3. 错误处理和重试

实现健壮的错误处理和重试机制：

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def safe_get_mcp_tools():
    from app.agents.confluence_agent import get_mcp_tools
    return await get_mcp_tools()

async def main():
    try:
        tools = await safe_get_mcp_tools()
    except Exception as e:
        logger.error("Failed to get MCP tools", error=str(e))
        raise
```

### 4. 并发处理最佳实践

使用 `asyncio.gather()` 并发执行多个搜索：

```python
import asyncio

async def parallel_searches(queries: list[str]):
    from app.agents.confluence_agent import get_mcp_tools
    
    tools = await get_mcp_tools()
    search_tool = next((t for t in tools if t.name == "confluence_search"), None)
    
    if not search_tool:
        raise ValueError("confluence_search tool not found")
    
    tasks = [
        search_tool.invoke({"query": q})
        for q in queries
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

### 5. 日志和监控

使用结构化日志便于问题排查和性能监控：

```python
from structlog.stdlib import get_logger

logger = get_logger(__name__)

# 记录关键事件
logger.info("agent_started", question="...", agent_type="research")
logger.info("search_completed", tool="confluence_search", result_count=10)
logger.warning("tool_not_found", tool_name="confluence_get_page")
logger.error("api_error", error="rate_limit_exceeded", retry_after=60)
```

### 6. 缓存和性能优化

合理使用全局缓存以减少开销：

```python
# 缓存自动管理，无需手动干预
from app.agents.confluence_agent import get_mcp_tools

# 首次调用：初始化和缓存
tools_1 = asyncio.run(get_mcp_tools())  # 慢

# 后续调用：直接返回缓存
tools_2 = asyncio.run(get_mcp_tools())  # 快

# 仅在需要时重置缓存
from app.agents.confluence_agent import reset_mcp_tools_cache
asyncio.run(reset_mcp_tools_cache())  # 清空缓存
```

### 7. 安全最佳实践

保护敏感信息（API 密钥、URL）：

```bash
# 不要提交敏感信息到版本控制
# .gitignore
.env
.mcp.json
./output/

# 使用环境变量管理密钥
export CONFLUENCE_TOKEN="your-secret-token"

# 日志中避免记录敏感信息
logger.info("connected_to_confluence")  # ✓ 安全
logger.info("token", token="abc123")    # ✗ 不安全
```

### 8. 测试策略

为 Agent 编写单元和集成测试：

```python
# tests/test_confluence_agent.py
import pytest
import asyncio
from app.agents.confluence_agent import get_mcp_tools, confluence_agent

@pytest.mark.asyncio
async def test_mcp_tools_initialization():
    """测试 MCP 工具初始化"""
    tools = await get_mcp_tools()
    assert isinstance(tools, dict)
    assert len(tools) > 0
    assert "confluence_search" in tools

def test_confluence_agent_creation():
    """测试 Research Agent 创建"""
    from app.agents.confluence_agent import confluence_agent
    assert confluence_agent is not None

@pytest.mark.asyncio
async def test_confluence_agent_invoke():
    """测试 Agent 调用（集成测试）"""
    result = confluence_agent.invoke({
        "messages": [{"role": "user", "content": "测试问题"}]
    })
    assert result is not None
    assert "messages" in result
```

---

## 总结

Confluence Agent 是一个功能强大的知识库助手，提供了两种使用模式：

1. **Research Agent**：深度研究，支持多轮迭代
2. **Universal QA Agent**：快速问答，高效响应

通过合理的配置和最佳实践应用，你可以将 Confluence Agent 集成到企业应用中，显著提升知识库的可用性和员工的工作效率。

有任何问题或建议，欢迎提交 Issue 或 PR！
