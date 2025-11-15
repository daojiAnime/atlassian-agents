import logging
import sys
from types import TracebackType

import structlog
from structlog.stdlib import get_logger
from structlog.types import EventDict, Processor

# logging.basicConfig(level=logging.INFO)
logger = get_logger()

# 单例初始化标志：确保日志系统仅初始化一次
_logging_configured = False


def drop_color_message_key(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:  # noqa: ARG001
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(json_logs: bool = False, log_level: str = "INFO") -> None:
    global _logging_configured

    # 如果已经配置过，直接返回，避免重复初始化
    if _logging_configured:
        return

    root_logger = logging.getLogger()

    # 清除所有现有的处理器
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S%Z.%f", utc=False)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        # structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        # 仅在 JSON 日志中重命名 `event` 为 `message`
        shared_processors.append(structlog.processors.EventRenamer("message"))
        # 仅在 JSON 日志中格式化异常信息
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=shared_processors
        + [
            # 为 `ProcessorFormatter` 准备事件字典
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor
    if json_logs:
        log_renderer = structlog.processors.JSONRenderer()
    else:
        log_renderer = structlog.dev.ConsoleRenderer(
            exception_formatter=structlog.dev.RichTracebackFormatter(show_locals=False)
        )

    formatter = structlog.stdlib.ProcessorFormatter(
        # 仅对不来自 structlog 的日志条目运行
        foreign_pre_chain=shared_processors,
        # 在预处理链之后对所有条目运行
        processors=[
            # 移除 _record & _from_structlog 元数据
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    # 创建并添加唯一的处理器
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # logger_name_list = [name for name in logging.root.manager.loggerDict]
    # rich.print(f"logger_name_list: {logger_name_list}")
    # for name, logger in logging.root.manager.loggerDict.items():
    #     if isinstance(logger, logging.PlaceHolder):
    #         continue
    #     logger.handlers.clear()
    #     logger.addHandler(handler)
    # for _log in ["uvicorn", "uvicorn.error"]:
    #     logging.getLogger(_log).handlers.clear()
    #     logging.getLogger(_log).propagate = True
    #
    logging.getLogger("uvicorn").handlers.clear()
    # logging.getLogger("uvicorn").addHandler(handler)
    # logging.getLogger("uvicorn").propagate = False
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers.clear()
    uvicorn_error.addHandler(handler)
    uvicorn_error.propagate = False
    uvicorn_error.setLevel(logging.ERROR)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(handler)
    uvicorn_access.setLevel(logging.INFO)
    uvicorn_access.propagate = False

    def handle_exception(
        exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    # 将自定义错误处理程序注册为全局异常处理程序
    sys.excepthook = handle_exception

    # 标记日志系统已初始化
    _logging_configured = True
