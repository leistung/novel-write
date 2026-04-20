from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.prompts import CONSISTENCY_PROMPTS

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
    def __init__(self, llm):
        super().__init__(llm)

    def check_consistency(self, chapter_content: str, previous_chapter_content: str, book: Dict[str, Any]) -> Dict[str, Any]:
        """检查章节连续性"""
        title = book.get('title', '未知')
        genre = book.get('genre', '未知')
        
        # 构建系统提示
        system_prompt = CONSISTENCY_PROMPTS["check_consistency"].format(
            title=title,
            genre=genre,
            chapter_content=chapter_content,
            previous_chapter_content=previous_chapter_content
        )
        
        # 构建用户提示
        user_prompt = "请检查章节的连续性和一致性。"
        
        # 创建提示词
        prompt = self.create_prompt(system_prompt, user_prompt)
        
        # 运行链
        response = self.run_chain(prompt)
        content = response['content']
        token_usage = response['token_usage']

        # 解析输出
        return self._parse_audit_response(content)

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
