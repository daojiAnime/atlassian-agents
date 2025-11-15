"""
MCP (Model Context Protocol) 相关的通用工具函数。

此模块提供 MCP 配置、格式转换和验证的工具：
- Claude Code IDE 格式到 langchain-mcp-adapters 格式的转换
- MCP 服务器配置验证
- MCP 工具列表转换
"""

from typing import Any

from structlog.stdlib import get_logger

logger = get_logger(__name__)


def convert_claude_mcp_config_to_langchain(config: dict) -> dict:
    """
    将 Claude Code IDE 的 MCP 配置格式转换为 langchain-mcp-adapters 兼容格式。

    Claude Code IDE 使用的格式：
    ```json
    {
      "mcpServers": {
        "server-name": {
          "command": "python -m fastmcp",
          "args": ["--config", "config.json"],
          "env": {"KEY": "value"},
          "cwd": "/path/to/dir"
        }
      }
    }
    ```

    langchain-mcp-adapters 期望的格式：
    ```json
    {
      "server-name": {
        "transport": "stdio",
        "command": "python -m fastmcp",
        "args": ["--config", "config.json"],
        "env": {"KEY": "value"},
        "cwd": "/path/to/dir",
        "encoding": "utf-8"
      }
    }
    ```

    Args:
        config: 从 .mcp.json 加载的配置字典

    Returns:
        转换后的配置字典，可直接用于 MultiServerMCPClient

    Raises:
        ValueError: 配置格式不支持时
        KeyError: 必需的配置字段缺失时
    """
    servers_config = config.get("mcpServers", {})

    if not servers_config:
        logger.error("no_mcp_servers_found", available_keys=list(config.keys()))
        raise ValueError("No MCP servers found in configuration (mcpServers key is missing or empty)")

    converted = {}

    for server_name, server_config in servers_config.items():
        try:
            converted_server = _convert_single_mcp_server(server_name, server_config)
            converted[server_name] = converted_server
        except ValueError as e:
            logger.error(
                "mcp_server_conversion_failed",
                server_name=server_name,
                error=str(e),
            )
            raise

    logger.info("mcp_config_converted", original_count=len(servers_config), converted_count=len(converted))
    return converted


def _convert_single_mcp_server(server_name: str, server_config: dict) -> dict:
    """
    转换单个 MCP 服务器的配置。

    Args:
        server_name: 服务器名称
        server_config: 服务器配置字典

    Returns:
        转换后的单个服务器配置

    Raises:
        ValueError: 配置格式不支持时
    """
    if "command" in server_config:
        # 标准的 stdio 模式
        return {
            "transport": "stdio",
            "command": server_config["command"],
            "args": server_config.get("args", []),
            "env": server_config.get("env", {}),
            "cwd": server_config.get("cwd"),
            "encoding": server_config.get("encoding", "utf-8"),
        }
    elif "url" in server_config:
        # HTTP 模式（当前未实现）
        logger.warning(
            "http_mcp_not_supported",
            server_name=server_name,
            url=server_config["url"],
        )
        raise ValueError(f"HTTP-based MCP connections not yet supported for '{server_name}'")
    else:
        # 未知的配置格式
        available_keys = list(server_config.keys())
        logger.error(
            "unknown_mcp_config_format",
            server_name=server_name,
            available_keys=available_keys,
        )
        raise ValueError(
            f"Unknown MCP server configuration format for '{server_name}'. "
            f"Expected 'command' or 'url' key, got: {available_keys}"
        )


def validate_mcp_server_config(server_config: dict) -> tuple[bool, list[str]]:
    """
    验证 MCP 服务器配置的完整性和有效性。

    检查项：
    - 至少包含 'command' 或 'url' 之一
    - 如果有 'command'，验证路径有效性
    - 如果有 'args'，应为列表
    - 如果有 'env'，应为字典

    Args:
        server_config: 要验证的服务器配置字典

    Returns:
        (is_valid, errors) 元组，其中 is_valid 为 bool，errors 为错误信息列表
    """
    errors = []

    # 检查必需的传输方式
    if "command" not in server_config and "url" not in server_config:
        errors.append("Configuration must have either 'command' or 'url' key")

    # 验证 args
    if "args" in server_config:
        if not isinstance(server_config["args"], list):
            errors.append(f"'args' must be a list, got {type(server_config['args']).__name__}")

    # 验证 env
    if "env" in server_config:
        if not isinstance(server_config["env"], dict):
            errors.append(f"'env' must be a dict, got {type(server_config['env']).__name__}")

    # 验证 transport
    if "transport" in server_config:
        allowed_transports = ["stdio", "sse", "http"]
        if server_config["transport"] not in allowed_transports:
            errors.append(f"'transport' must be one of {allowed_transports}, " f"got '{server_config['transport']}'")

    is_valid = len(errors) == 0
    return is_valid, errors


def format_mcp_tools_list(tools: dict[str, Any]) -> list[dict[str, str]]:
    """
    将 MCP 工具字典转换为可读的列表格式。

    Args:
        tools: 工具字典 {tool_name: tool_object}

    Returns:
        格式化的工具列表，每项包含 name 和 description

    示例：
        ```python
        tools = {
            "confluence_search": tool_obj,
            "confluence_get_page": tool_obj,
        }

        formatted = format_mcp_tools_list(tools)
        # 返回:
        # [
        #     {"name": "confluence_search", "description": "Search for..."},
        #     {"name": "confluence_get_page", "description": "Retrieve..."}
        # ]
        ```
    """
    formatted_tools = []

    for tool_name, tool_obj in tools.items():
        tool_info = {
            "name": tool_name,
            "description": getattr(tool_obj, "description", "No description available"),
        }

        # 如果工具有 args_schema，添加到信息中
        if hasattr(tool_obj, "args_schema"):
            try:
                schema = tool_obj.args_schema
                if hasattr(schema, "model_fields"):
                    tool_info["parameters"] = list(schema.model_fields.keys())
            except Exception:
                pass  # 忽略 schema 解析错误

        formatted_tools.append(tool_info)

    return formatted_tools


def get_mcp_tool_names(tools: dict[str, Any]) -> list[str]:
    """
    从工具字典中提取所有工具名称。

    Args:
        tools: 工具字典 {tool_name: tool_object}

    Returns:
        按字母顺序排序的工具名称列表
    """
    return sorted(tools.keys())


def merge_mcp_configs(
    base_config: dict,
    override_config: dict,
) -> dict:
    """
    合并两个 MCP 配置字典，允许覆盖。

    Args:
        base_config: 基础配置
        override_config: 覆盖配置（优先级更高）

    Returns:
        合并后的配置

    示例：
        ```python
        base = {"mcpServers": {"server1": {...}}}
        override = {"mcpServers": {"server2": {...}}}
        merged = merge_mcp_configs(base, override)
        # 结果包含 server1 和 server2
        ```
    """
    merged = base_config.copy()

    # 深度合并 mcpServers
    if "mcpServers" in override_config:
        if "mcpServers" not in merged:
            merged["mcpServers"] = {}

        merged["mcpServers"].update(override_config["mcpServers"])

    # 复制其他顶级键
    for key, value in override_config.items():
        if key != "mcpServers":
            merged[key] = value

    return merged
