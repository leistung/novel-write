from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient
from src.agents.prompts.prompts import CHECKER_PROMPTS

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

    def check_continuity(self, book_title: str, chapter_num: int, chapter_content: str, previous_summary: str, current_state: str) -> Dict[str, Any]:
        """检查章节连续性"""
        # 构建系统提示
        system_prompt = "你是一位专业的小说连续性审计员，擅长检查小说章节的连续性、逻辑性和一致性。你的任务是全面检查章节内容，确保其与前章内容和当前状态保持一致。"
        
        # 构建用户提示
        user_prompt = CHECKER_PROMPTS["check_continuity"].format(
            book_title=book_title,
            chapter_num=chapter_num,
            chapter_content=chapter_content,
            previous_summary=previous_summary,
            current_state=current_state
        )

        # 调用 LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm_client.chat_completion(messages)

        # 解析输出
        return self._parse_audit_response(response)

    def run(self, context: AgentContext) -> Dict[str, Any]:
        """运行连续性审计"""
        book_title = context.kwargs.get('book_title', '未知')
        chapter_num = context.chapter_num
        chapter_content = context.kwargs.get('chapter_content', '无')
        previous_summary = context.kwargs.get('previous_summary', '无')
        current_state = context.kwargs.get('current_state', '无')

        return self.check_continuity(book_title, chapter_num, chapter_content, previous_summary, current_state)

    def _parse_audit_response(self, response: str) -> Dict[str, Any]:
        """解析审计响应"""
        # 从响应中提取评分
        import re
        score_match = re.search(r'总体评分：(\d+\.?\d*)', response)
        if score_match:
            score = float(score_match.group(1))
        else:
            # 如果没有找到评分，默认给75分
            score = 75.0
        
        # 从响应中提取问题
        issues = []
        issues_match = re.findall(r'问题：(.*?)严重程度：(.*?)(?=问题：|$)', response, re.DOTALL)
        for i, (message, severity) in enumerate(issues_match):
            # 简单处理，实际应该更复杂
            issues.append(AuditIssue(str(i+1), "连续性问题", severity.strip(), message.strip(), "未知位置"))
        
        # 检查是否通过
        passed = score >= 70.0

        return {
            "score": score,
            "issues": [issue.__dict__ for issue in issues],
            "passed": passed,
            "analysis": response
        }
