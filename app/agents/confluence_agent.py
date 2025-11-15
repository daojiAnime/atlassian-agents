import asyncio
import json
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from structlog.stdlib import get_logger

from app.core.config import settings

logger = get_logger(__name__)


# ============================================================================
# MCP Client Initialization
# ============================================================================

# Global MCP client instance (lazy initialization)
_mcp_client: MultiServerMCPClient | None = None

# Global MCP tools cache (lazy initialization with caching)
_mcp_tools_cache: dict[str, dict] | None = None


def _load_mcp_config(config_path: Path) -> dict:
    """
    同步函数：从文件系统加载 MCP 配置。

    这个函数被设计为在线程池中运行，以避免在异步上下文中阻塞事件循环。

    Args:
        config_path: .mcp.json 配置文件的路径

    Returns:
        解析后的配置字典

    Raises:
        FileNotFoundError: 配置文件不存在时
        json.JSONDecodeError: JSON 解析失败时
    """
    with config_path.open() as f:
        return json.load(f)


def _convert_mcp_json_config(config: dict) -> dict:
    """
    Convert the Claude Code IDE .mcp.json format to langchain-mcp-adapters format.

    The Claude Code IDE uses a different format than langchain-mcp-adapters requires.
    This function converts between them.

    Args:
        config: Configuration from .mcp.json (Claude Code IDE format)

    Returns:
        Configuration dictionary compatible with MultiServerMCPClient
    """
    servers_config = config.get("mcpServers", {})
    converted = {}

    for server_name, server_config in servers_config.items():
        # Claude Code IDE format uses "command" + "args" for stdio
        # langchain-mcp-adapters expects explicit transport key
        if "command" in server_config:
            # Convert stdio/docker command format for langchain-mcp-adapters
            converted[server_name] = {
                "transport": "stdio",  # Explicitly specify stdio transport
                "command": server_config["command"],
                "args": server_config.get("args", []),
                "env": server_config.get("env", {}),
                "cwd": server_config.get("cwd"),
                "encoding": server_config.get("encoding", "utf-8"),
            }
        elif "url" in server_config:
            # If there's a URL, it might be HTTP-based (future use)
            # For now, we focus on stdio connections
            raise ValueError(f"HTTP-based connections not yet supported for {server_name}")
        else:
            raise ValueError(f"Unknown server configuration format for {server_name}")

    return converted


_mcp_client: MultiServerMCPClient | None = None
_mcp_client_lock = asyncio.Lock()


async def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client

    if _mcp_client is not None:
        return _mcp_client

    async with _mcp_client_lock:
        if _mcp_client is not None:
            return _mcp_client

        config_path = Path(".mcp.json")
        config = await asyncio.to_thread(_load_mcp_config, config_path)
        servers = _convert_mcp_json_config(config)
        _mcp_client = MultiServerMCPClient(servers)
        return _mcp_client


async def _fetch_all_mcp_tools() -> dict[str, dict]:
    """
    从 MCP 服务器获取所有可用工具。

    此函数仅在首次初始化时调用。结果会被缓存供后续使用。

    Returns:
        工具名称到工具对象的字典映射

    Raises:
        ValueError: 如果没有找到任何工具
    """
    client = await get_mcp_client()
    all_tools = await client.get_tools(server_name="mcp-atlassian")

    if not all_tools:
        logger.error("no_tools_found_in_mcp_server")
        raise ValueError("No tools found in MCP server")

    tools_dict = {tool.name: tool for tool in all_tools}
    tool_names = list(tools_dict.keys())
    logger.info("mcp_tools_fetched", tool_names=tool_names, tool_count=len(tools_dict))
    return tools_dict


async def get_mcp_tools() -> dict[str, dict]:
    """
    获取 MCP tools 字典（带缓存）。

    采用延迟初始化 + 缓存策略：
    - 首次调用时从 MCP 服务器获取所有 tools
    - 后续调用直接返回缓存的 tools
    - 避免重复创建 session 和 I/O 操作

    Returns:
        缓存的工具字典 {tool_name: tool_object}

    Raises:
        ValueError: 初始化失败时
    """
    global _mcp_tools_cache

    if _mcp_tools_cache is None:
        logger.info("Initializing MCP tools cache")
        try:
            _mcp_tools_cache = await _fetch_all_mcp_tools()
            logger.info("mcp_tools_cache_initialized", tool_count=len(_mcp_tools_cache))
        except Exception:
            logger.exception("Failed to initialize MCP tools cache")
            raise

    return _mcp_tools_cache


async def reset_mcp_tools_cache() -> None:
    """
    重置 MCP tools 缓存。

    在以下情况调用此函数：
    - MCP 服务器配置变化
    - 需要热重载 tools
    - 调试和开发时

    该函数是非阻塞的，不会立即重新初始化缓存。
    下一次调用 get_mcp_tools() 时会自动重新加载。
    """
    global _mcp_tools_cache
    _mcp_tools_cache = None
    logger.info("mcp_tools_cache_reset")


_mcp_init_task: asyncio.Task | None = None


async def _initialize_mcp_tools_async():
    """实际异步初始化逻辑"""
    try:
        logger.info("Initializing MCP tools (async)...")
        await get_mcp_tools()
        logger.info("MCP tools initialized")
    except FileNotFoundError as e:
        logger.warning(
            "mcp_config_not_found_during_init",
            error=str(e),
            details="MCP tools will be initialized on first use",
        )
    except Exception as e:
        logger.warning(
            "mcp_tools_initialization_failed",
            error=str(e),
            details="MCP tools will be initialized on first use",
        )


def initialize_mcp_tools_on_import():
    """
    在模块加载阶段调用，不执行 await，只启动后台任务，不阻塞。
    """
    global _mcp_init_task
    try:
        loop = asyncio.get_event_loop()
        _mcp_init_task = loop.create_task(_initialize_mcp_tools_async())
        logger.info("Scheduled MCP tools initialization task")
    except RuntimeError:
        # 如果还没有事件循环，就等到第一次 async 初始化再启动
        logger.info("No running event loop; MCP tools will initialize on demand")
        _mcp_init_task = None


# ============================================================================
# Tool Getter Functions
# ============================================================================


async def get_confluence_tools() -> list:
    """
    获取 Confluence 相关的 MCP 工具列表。

    直接从 MCP 服务器获取工具，不进行额外封装。
    Agent 框架会自动处理异步调用。

    Returns:
        Confluence 相关工具的列表

    Raises:
        ValueError: 如果找不到所需工具
    """
    tools_dict = await get_mcp_tools()

    # 定义需要的工具
    required_tools = ["confluence_search", "confluence_get_page", "confluence_get_comments"]

    confluence_tools = []
    for tool_name in required_tools:
        tool = tools_dict.get(tool_name)
        if not tool:
            logger.warning("confluence_tool_not_found", tool_name=tool_name)
        else:
            confluence_tools.append(tool)

    if not confluence_tools:
        logger.error("no_confluence_tools_found")
        raise ValueError("No Confluence tools found in MCP server")

    logger.info("confluence_tools_fetched", tool_count=len(confluence_tools))
    return confluence_tools


# ============================================================================
# Sub-Agent Configurations
# ============================================================================

sub_research_prompt = """You are a dedicated researcher specializing in enterprise knowledge bases.
Your job is to conduct thorough research using the Confluence knowledge base to answer user questions.

You have access to Confluence search and page retrieval tools. Use them to:
1. Search for relevant documents using keywords and natural language queries
2. Retrieve complete page content when you need detailed information
3. Cross-reference information across multiple Confluence pages

Conduct thorough research and then reply to the user with a detailed answer to their question.

Only your FINAL answer will be passed on to the user. They will have NO knowledge of anything except
your final message, so your final report should be your final message!

Important notes:
- Confluence is an internal enterprise knowledge base, not the internet
- All search results are from internal documentation
- When citing information, include the Confluence page title and/or URL
- If a search returns no results, try rephrasing your query with different keywords"""


async def _build_research_sub_agent():
    """构建研究子代理配置（异步）"""
    tools = await get_confluence_tools()
    return {
        "name": "confluence-research-agent",
        "description": "Used to research in-depth questions using the Confluence knowledge base. Only give this researcher one topic at a time. Do not pass multiple sub questions to this researcher. Instead, break down a large topic into necessary components and call multiple research agents in parallel, one for each sub-question.",
        "system_prompt": sub_research_prompt,
        "tools": tools,
    }


sub_critique_prompt = """You are a dedicated editor and quality reviewer specializing in corporate knowledge management.
You are being tasked to critique a research report generated from Confluence documentation.

You can find the report at `final_report.md`.
You can find the question/topic for this report at `question.txt`.

The user may ask for specific areas to critique the report in. Respond with a detailed critique of the report,
highlighting things that could be improved.

You can use the Confluence search tool to verify facts and find additional supporting information if needed.

Do not write to the `final_report.md` yourself.

Things to check:
- Check that each section is appropriately named
- Check that the report is written as you would find in an essay or a textbook - it should be text heavy, not just bullet points!
- Check that the report is comprehensive. If any paragraphs or sections are short or missing important details, point it out.
- Check that the article covers key areas and ensures overall understanding without omitting important parts.
- Check that the article deeply analyzes causes, impacts, and trends, providing valuable insights
- Check that the article closely follows the research topic and directly answers questions
- Check that the article has a clear structure, fluent language, and is easy to understand.
- Verify that all citations and references to Confluence documents are accurate
"""


async def _build_critique_sub_agent():
    """构建评论子代理配置（异步）"""
    tools = await get_confluence_tools()
    # 评论代理只需要搜索工具
    search_tool = next((t for t in tools if t.name == "confluence_search"), tools[0])
    return {
        "name": "confluence-critique-agent",
        "description": "Used to critique the final report based on Confluence research. Provide this agent with specific information about how you want it to critique the report.",
        "system_prompt": sub_critique_prompt,
        "tools": [search_tool],
    }


# ============================================================================
# Main Agent Configuration
# ============================================================================

confluence_research_instructions = """You are an expert researcher specializing in enterprise knowledge management.
Your job is to conduct thorough research in the Confluence knowledge base, and then write a polished report.

The first thing you should do is to write the original user question to `question.txt` so you have a record of it.

Use the confluence-research-agent to conduct deep research. It will respond to your questions/topics with detailed answers
from the Confluence knowledge base.

When you have enough information to write a final report, write it to `final_report.md`.

You can call the confluence-critique-agent to get a critique of the final report. After that (if needed),
you can do more research and edit the `final_report.md`. You can do this as many times as you want until you are satisfied.

Only edit the file once at a time (if you call this tool in parallel, there may be conflicts).

Here are instructions for writing the final report:

<report_instructions>

CRITICAL: Make sure the answer is written in the same language as the human messages!
If you make a todo plan - you should note in the plan what language the report should be in so you dont forget!
Note: the language the report should be in is the language the QUESTION is in, not the language/country that the question is ABOUT.

Please create a detailed answer to the overall research brief that:
1. Is well-organized with proper headings (# for title, ## for sections, ### for subsections)
2. Includes specific facts and insights from the research
3. References relevant Confluence pages using [Title](URL) format
4. Provides a balanced, thorough analysis. Be as comprehensive as possible and include all information relevant to the research question. Users are conducting deep research and will expect detailed, comprehensive answers.
5. Includes a "Sources" section at the end with all referenced links and Confluence pages

You can structure your report in different ways. Here are some examples:

To answer a question that asks you to compare two things:
1/ intro
2/ overview of topic A
3/ overview of topic B
4/ comparison between A and B
5/ conclusion

To answer a question that asks you to return a list of things:
1/ list of things or table of things
Or, you could make each item in the list a separate section. When asked for lists, you don't need an introduction or conclusion.
1/ item 1
2/ item 2
3/ item 3

To answer a question that asks you to summarize a topic or give an overview:
1/ overview of topic
2/ concept 1
3/ concept 2
4/ concept 3
5/ conclusion

If you think you can answer the question with a single section, you can do that too!
1/ answer

REMEMBER: Section is a VERY fluid and loose concept. You can structure your report however you think is best!
Make sure that your sections are cohesive and make sense for the reader.

For each section of the report, do the following:
- Use simple, clear language
- Use ## for section title (Markdown format) for each section of the report
- Do NOT ever refer to yourself as the writer of the report. This should be a professional report without any self-referential language.
- Do not say what you are doing in the report. Just write the report without any commentary from yourself.
- Each section should be as long as necessary to deeply answer the question with the information gathered. Sections are expected to be fairly long and verbose. Users expect thorough answers.
- Use bullet points to list out information when appropriate, but by default, write in paragraph form.

REMEMBER:
The research is from an internal Confluence knowledge base. Make sure the final answer report is in the SAME language
as the human messages in the message history.

Format the report in clear markdown with proper structure and include source references where appropriate.

<Citation Rules>
- Assign each unique URL/page a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list
- Each source should be a separate line item in a list, so that in markdown it is rendered as a list.
- Example format:
  [1] Page Title: https://docs.weepal.info/pages/viewpage.action?pageId=123456
  [2] Another Page: https://docs.weepal.info/pages/viewpage.action?pageId=789012
- Citations are extremely important. Make sure to include these and pay attention to getting them right.
  Users will use these citations to review the original Confluence documentation.
</Citation Rules>
</report_instructions>

You have access to tools for researching in the Confluence knowledge base:

## `confluence_search`
Use this to search for documents in the Confluence knowledge base. You can specify search terms and optionally filter by space.

## `get_confluence_page`
Use this to retrieve the complete content of a specific Confluence page after you've found it via search.

## `get_confluence_comments`
Use this to retrieve discussion and comments on a Confluence page for additional context.
"""

# ============================================================================
# Agent Factory
# ============================================================================


async def create_confluence_research_agent_async():
    """
    异步创建 Confluence 研究代理。
    """
    llm = init_chat_model(model=settings.INIT_LLM_MODEL)
    tools = await get_confluence_tools()

    # 异步构建子代理
    research_sub_agent = await _build_research_sub_agent()
    critique_sub_agent = await _build_critique_sub_agent()

    return create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=confluence_research_instructions,
        subagents=[critique_sub_agent, research_sub_agent],
        backend=FilesystemBackend(root_dir="./output"),
    )
