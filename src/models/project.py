from pydantic import BaseModel
from typing import Optional, List, Dict
from .book import Platform, Genre, BookStatus, FanficMode

class LLMConfig(BaseModel):
    provider: str
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 8192

class NotifyChannel(BaseModel):
    type: str  # telegram, feishu, wechat, webhook
    config: Dict[str, str]

class DetectionConfig(BaseModel):
    enabled: bool = True
    threshold: float = 0.5

class QualityGates(BaseModel):
    min_audit_score: float = 0.7
    max_ai_tells: int = 5
    max_sensitive_words: int = 0

class AgentLLMOverride(BaseModel):
    agent: str  # writer, auditor, reviser, architect, radar
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

class ProjectConfig(BaseModel):
    project_name: str
    llm: LLMConfig
    notify: Optional[List[NotifyChannel]] = None
    detection: DetectionConfig = DetectionConfig()
    quality_gates: QualityGates = QualityGates()
    agent_llm_overrides: Optional[Dict[str, AgentLLMOverride]] = None
