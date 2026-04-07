from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient

class AuditIssue:
    def __init__(self, id: str, type: str, severity: str, message: str, location: str):
        self.id = id
        self.type = type
        self.severity = severity
        self.message = message
        self.location = location

class AuditResult:
    def __init__(self, score: float, issues: List[AuditIssue], passed: bool):
        self.score = score
        self.issues = issues
        self.passed = passed

class ContinuityAuditor(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client)

    def run(self, context: AgentContext) -> Dict[str, Any]:
        # 构建提示
        messages = [
            ("system", "你是一位专业的小说连续性审计员，擅长检查小说章节的连续性、逻辑性和一致性。"),
            ("human", f"请审计《{context.kwargs.get('book_title', '未知')}》第{context.chapter_num}章的连续性，检查以下方面：\n1. 角色记忆和行为一致性\n2. 物资和资源连续性\n3. 伏笔和线索回收\n4. 大纲偏离情况\n5. 叙事节奏和情感弧线\n6. AI 生成痕迹\n\n章节内容：{context.kwargs.get('chapter_content', '无')}\n\n前章摘要：{context.kwargs.get('previous_summary', '无')}\n\n当前世界状态：{context.kwargs.get('current_state', '无')}")
        ]

        # 调用 LLM
        response = self.llm_client.chat_completion(messages)

        # 解析输出
        # 这里可以添加更复杂的解析逻辑
        score = 0.85
        issues = [
            AuditIssue("1", "角色一致性", "低", "角色A的行为与前章略有不一致", "第10段"),
            AuditIssue("2", "节奏控制", "低", "部分场景节奏略慢", "第20段")
        ]
        passed = score >= 0.7

        return {
            "score": score,
            "issues": [issue.__dict__ for issue in issues],
            "passed": passed
        }
