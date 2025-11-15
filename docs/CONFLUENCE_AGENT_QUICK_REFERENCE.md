# Confluence Agent 快速参考

## 1. 导入和使用

### 使用 Research Agent（深度研究）

```python
from app.agents.confluence_agent import confluence_agent

result = confluence_agent.invoke({
    "messages": [{"role": "user", "content": "请研究..."}]
})
```

### 使用 Universal QA Agent（快速问答）

```python
from app.agents.universal_assistant import universal_qa_agent

result = universal_qa_agent.invoke({
    "messages": [{"role": "user", "content": "什么是...？"}]
})
```

---

## 2. 配置文件

### .mcp.json（MCP 服务器配置）

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

### .env（应用配置）

```env
INIT_LLM_MODEL=openai:deepseek-ai/DeepSeek-V3.2-Exp
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
RERANK_MODEL=Qwen/Qwen3-Reranker-8B
```

---

## 3. 核心 API

| 函数 | 说明 | 异步 |
|------|------|------|
| `get_mcp_client()` | 获取 MCP 客户端 | ✓ |
| `get_mcp_tools()` | 获取工具字典 | ✓ |
| `reset_mcp_tools_cache()` | 重置缓存 | ✓ |
| `create_confluence_research_agent()` | 创建 Research Agent | ✗ |
| `create_universal_qa_agent()` | 创建 QA Agent | ✗ |

---

## 4. 项目结构

```
app/
├── agents/
│   ├── confluence_agent.py       # MCP 集成 + Research Agent
│   └── universal_assistant.py    # Universal QA Agent
├── core/
│   ├── config.py                # 配置管理
│   └── log_adapter.py            # 日志初始化
main.py                           # 启动入口
docs/
├── CONFLUENCE_AGENT_GUIDE.md     # 完整指南
└── CONFLUENCE_AGENT_QUICK_REFERENCE.md  # 本文件
```

---

## 5. 常见任务

### 初始化应用（启动时）

```python
from app.core.log_adapter import setup_logging
from app.agents.confluence_agent import initialize_mcp_tools_sync

setup_logging()
initialize_mcp_tools_sync()
```

### 检查可用工具

```python
import asyncio
from app.agents.confluence_agent import get_mcp_tools

async def check_tools():
    tools = await get_mcp_tools()
    for name in tools.keys():
        print(name)

asyncio.run(check_tools())
```

### 并发执行多个研究

```python
import asyncio
from app.agents.confluence_agent import confluence_agent

async def parallel_research():
    tasks = [
        asyncio.to_thread(
            confluence_agent.invoke,
            {"messages": [{"role": "user", "content": q}]}
        )
        for q in ["问题1", "问题2", "问题3"]
    ]
    return await asyncio.gather(*tasks)

results = asyncio.run(parallel_research())
```

---

## 6. 故障排查速查表

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `FileNotFoundError: .mcp.json` | 配置文件不存在 | 创建 `.mcp.json` 在项目根目录 |
| `mcp_client_initialization_failed` | MCP 服务器连接失败 | 检查服务器进程、env 变量 |
| `no_confluence_tools_found` | 工具加载失败 | 验证 MCP 服务器输出正确工具 |
| `asyncio.run() cannot be called from running event loop` | 事件循环冲突 | 使用 `await` 而非 `asyncio.run()` |
| `PermissionError: ./output/` | 目录权限不足 | `chmod 755 ./output` |

---

## 7. Agent 选择指南

### 何时使用 Research Agent

- 需要深度研究和分析
- 允许较长响应时间（1-5 分钟）
- 需要自动质量评审
- 希望生成专业报告格式

### 何时使用 Universal QA Agent

- 快速回答简单问题
- 要求快速响应（<20秒）
- 员工日常咨询
- 知识库常见问题

---

## 8. 系统提示词示例

### Research Agent 的核心约束

```
1. 记录原始问题到 question.txt
2. 使用 confluence-research-agent 进行深度搜索
3. 综合信息生成 final_report.md
4. 可选：调用 confluence-critique-agent 进行评审
5. 根据反馈迭代修改（单次）
6. 使用与用户相同的语言
7. 包含完整的来源引用
```

### Universal QA Agent 的核心约束

```
1. 分析问题类型和复杂度
2. 智能规划最优搜索策略
3. 避免重复搜索
4. 生成清晰的 Markdown 答案
5. 包含参考资源
6. 20 秒内完成
```

---

## 9. 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `INIT_LLM_MODEL` | `openai:deepseek-ai/DeepSeek-V3.2-Exp` | 初始化 LLM 模型 |
| `LLM_MODEL` | `deepseek-ai/DeepSeek-V3.2-Exp` | 推理 LLM 模型 |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-8B` | 向量化模型 |
| `RERANK_MODEL` | `Qwen/Qwen3-Reranker-8B` | 重排序模型 |
| `RERANK_BASE_URL` | `https://api.siliconflow.cn/v1/rerank` | 重排序 API |
| `UPLOAD_DIR` | `/app/uploads` | 文件上传目录 |

---

## 10. 输出文件位置

Research Agent 生成的中间文件存储在 `./output/`：

- `question.txt`：原始提问内容
- `final_report.md`：最终研究报告（Markdown 格式）

---

## 11. 日志记录示例

```python
from structlog.stdlib import get_logger

logger = get_logger(__name__)

logger.info("operation_started", question="...")
logger.warning("tool_missing", tool_name="confluence_search")
logger.error("api_error", error="timeout", retry_count=3)
```

---

## 12. 技术栈版本

| 库 | 最低版本 |
|----|----------|
| deepagents | 0.2.6 |
| langchain | 1.0.5 |
| langgraph-cli | 0.4.7 |
| langchain-mcp-adapters | 0.1.12 |
| langchain-openai | 1.0.2 |
| pydantic-settings | 2.10.1 |
| structlog | 25.4.0 |

---

## 13. 关键设计原则

### 全局单例 + 延迟初始化

```
_mcp_client: MultiServerMCPClient | None = None
_mcp_tools_cache: dict[str, dict] | None = None
```

只在首次使用时初始化，后续调用返回缓存。

### 子代理分工

```
Main Agent
├─ research-sub-agent  (搜索 + 信息提取)
└─ critique-sub-agent  (质量评审)
```

### 异步/同步兼容

- 内部异步（async/await）
- 启动同步包装（asyncio.run）
- 运行时支持两种调用方式

---

## 14. 文件系统后端

Research Agent 使用 `FilesystemBackend` 处理中间文件：

```python
backend=FilesystemBackend(root_dir="./output")
```

**特点**：
- 自动管理文件生命周期
- 支持多轮迭代（追加而非覆盖）
- 可用于调试和审计

---

## 15. 常用命令

```bash
# 启动应用
langgraph up --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/

# 代码检查
ruff check app/

# 安装依赖
uv sync

# 查看日志
tail -f application.log
```

---

## 相关资源

- 完整指南：[CONFLUENCE_AGENT_GUIDE.md](./CONFLUENCE_AGENT_GUIDE.md)
- 上下文摘要：[.claude/context-summary-confluence-agent.md](../.claude/context-summary-confluence-agent.md)
- 源代码：[app/agents/confluence_agent.py](../app/agents/confluence_agent.py)

---

**最后更新**：2025-11-14

**维护者**：Atlassian Agents 开发团队
