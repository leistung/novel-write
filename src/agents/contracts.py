from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentRunResult:
    """统一的 Agent 执行结果，用于工作流节点之间传递可审计信息。"""

    ok: bool
    task: str
    data: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    feedback: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw: Any = None

    def to_state(self, key: str) -> Dict[str, Any]:
        return {
            key: self.data,
            f"{key}_ok": self.ok,
            f"{key}_score": self.score,
            f"{key}_feedback": self.feedback,
            f"{key}_errors": self.errors,
            f"{key}_warnings": self.warnings,
        }
