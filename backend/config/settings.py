"""应用配置管理 - 企业级安全配置"""
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from pydantic import Field, field_validator, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 - 支持多环境隔离"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )
    
    # ==================== 环境配置 ====================
    APP_NAME: str = Field(default="NovelWrite", description="应用名称")
    ENV: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # ==================== 安全配置 ====================
    # 强制生成随机密钥，避免硬编码（开发环境使用固定默认值）
    SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr("dev-secret-key-do-not-use-in-production")
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=1440)
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS来源列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # ==================== 数据库配置 ====================
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/novel_write.db")
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5, le=300)
    
    @property
    def DATABASE_URL_FOR_ENV(self) -> str:
        """根据环境返回对应的数据库URL"""
        if self.ENV == "production":
            # 生产环境必须使用PostgreSQL
            if "postgresql" not in self.DATABASE_URL:
                raise ValueError("Production environment must use PostgreSQL")
            return self.DATABASE_URL
        elif self.ENV == "testing":
            # 测试环境使用内存数据库
            return "sqlite+aiosqlite:///:memory:"
        return self.DATABASE_URL
    
    # ==================== LLM配置（使用SecretStr保护密钥）====================
    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None)
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1")
    OPENAI_MODEL: str = Field(default="gpt-4o")
    
    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(default=None)
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229")
    
    DEFAULT_LLM_PROVIDER: str = Field(default="openai", pattern="^(openai|anthropic)$")
    
    # 兼容旧版配置格式
    LLM_API_KEY: Optional[SecretStr] = Field(default=None)
    LLM_BASE_URL: Optional[str] = Field(default=None)
    LLM_MODEL: Optional[str] = Field(default=None)
    LLM_PROVIDER: Optional[str] = Field(default=None)
    LLM_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=8192, ge=100, le=32000)
    
    # LLM调用限制
    LLM_MAX_RETRIES: int = Field(default=3, ge=1, le=10)
    LLM_TIMEOUT_SECONDS: int = Field(default=120, ge=10, le=600)
    LLM_RATE_LIMIT_RPM: int = Field(default=60, ge=1, le=1000)  # 每分钟请求限制
    
    # ==================== 存储配置 ====================
    STORE_PATH: Path = Field(default=Path("./store"))
    CHECKPOINT_PATH: Path = Field(default=Path("./data/checkpoints"))
    
    # ==================== RAG配置 ====================
    CHROMA_PERSIST_DIR: str = Field(default="./data/chroma")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    
    # ==================== Redis配置（用于Celery和缓存）====================
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = Field(default=3600, ge=60, le=86400)
    
    # ==================== Celery配置 ====================
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)
    
    @property
    def CELERY_CONFIG(self) -> dict:
        """Celery配置"""
        broker = self.CELERY_BROKER_URL or self.REDIS_URL
        backend = self.CELERY_RESULT_BACKEND or self.REDIS_URL
        return {
            "broker_url": broker,
            "result_backend": backend,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "Asia/Shanghai",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": 3600,
            "worker_prefetch_multiplier": 1,
        }
    
    # ==================== MCP配置 ====================
    MCP_SERVER_URL: str = Field(default="http://localhost:3000")
    ENABLE_MCP: bool = Field(default=False)
    
    # ==================== WebSocket配置 ====================
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, ge=10, le=300)
    
    # ==================== 监控配置 ====================
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090, ge=1000, le=65535)
    
    # ==================== 生产环境强制检查 ====================
    @model_validator(mode='after')
    def validate_production(self):
        """生产环境强制安全检查"""
        if self.ENV == "production":
            # 检查密钥
            secret_value = self.SECRET_KEY.get_secret_value()
            if len(secret_value) < 32 or "change-this" in secret_value.lower():
                raise ValueError(
                    "Production environment requires a strong SECRET_KEY. "
                    "Please set a secure random key in environment variables."
                )
            
            # 检查LLM配置
            if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                raise ValueError(
                    "Production environment requires at least one LLM API key"
                )
            
            # 强制关闭DEBUG
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")
            
            # 检查数据库
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    "SQLite is not recommended for production. "
                    "Please use PostgreSQL."
                )
        
        return self
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 映射旧版配置到新版
        self._migrate_legacy_config()
    
    def _migrate_legacy_config(self):
        """迁移旧版配置格式到新版"""
        # 映射简化格式到标准格式
        if self.LLM_API_KEY and not self.OPENAI_API_KEY:
            self.OPENAI_API_KEY = self.LLM_API_KEY
        if self.LLM_BASE_URL and self.OPENAI_BASE_URL == "https://api.openai.com/v1":
            self.OPENAI_BASE_URL = self.LLM_BASE_URL
        if self.LLM_MODEL and self.OPENAI_MODEL == "gpt-4o":
            self.OPENAI_MODEL = self.LLM_MODEL
        if self.LLM_PROVIDER and self.DEFAULT_LLM_PROVIDER == "openai":
            self.DEFAULT_LLM_PROVIDER = self.LLM_PROVIDER
    
    def _ensure_paths(self):
        """确保必要路径存在"""
        self.STORE_PATH.mkdir(parents=True, exist_ok=True)
        self.CHECKPOINT_PATH.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)
    
    # ==================== 便捷属性 ====================
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENV == "production"
    
    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENV == "development"
    
    @property
    def IS_TESTING(self) -> bool:
        return self.ENV == "testing"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    s = Settings()
    s._ensure_paths()
    return s


# 导出配置实例
settings = get_settings()
