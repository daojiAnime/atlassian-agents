from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从环境变量和 .env 文件加载配置"""

    model_config = SettingsConfigDict(
        # 验证默认值是否正确
        validate_default=False,
        # 优先级：后面文件的配置会覆盖前面文件的配置
        env_file=[".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        # 忽略未定义的配置
        extra="ignore",
    )

    # ==================== 模型配置 ====================
    INIT_LLM_MODEL: str = "openai:deepseek-ai/DeepSeek-V3.2-Exp"
    VL_MODEL_NAME: str = "Qwen/Qwen3-VL-32B-Instruct"

    UPLOAD_DIR: str = "/app/uploads"
    """文件上传临时目录，用于存储待处理的文档和图片"""

    # ==================== 向量和排序模型 ====================
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-8B"
    """向量化模型，用于文档相似度检索"""

    RERANK_MODEL: str = "Qwen/Qwen3-Reranker-8B"
    """重排序模型，用于优化检索结果排序"""

    LLM_MODEL: str = "deepseek-ai/DeepSeek-V3.2-Exp"
    """大语言模型，用于复杂推理任务"""

    # ==================== API 端点配置 ====================
    RERANK_BASE_URL: str = "https://api.siliconflow.cn/v1/rerank"
    """重排序 API 端点"""


settings: Settings = Settings()  # type: ignore
