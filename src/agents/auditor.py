from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient
from src.agents.prompts.prompts import AUTHOR_PROMPTS

class AuditorAgent(BaseAgent):
    """审核Agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client)
    
    def score_chapter(self, content: str, book: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        """给章节打分"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        writing_style = book.get('writing_style', '')
        
        # 构建系统提示
        system_prompt = AUTHOR_PROMPTS["score_chapter"].format(
            genre=genre,
            chapter_num=chapter_num,
            platform=platform,
            chapter_word_count=chapter_word_count,
            writing_style=writing_style if writing_style else '无特殊要求'
        )
        
        # 构建用户提示
        user_prompt = f"请审核以下章节内容：\n\n{content}"
        
        # 调用 LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm_client.chat_completion(messages)
        
        # 解析审核结果
        return self._parse_audit_result(response, content, chapter_word_count, genre, platform)
    
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """运行审核"""
        content = input.get('content', '')
        book = input.get('book', {})
        chapter_num = input.get('chapter_num', 1)
        
        # 审核内容
        return self.score_chapter(content, book, chapter_num)
    
    def _parse_audit_result(self, response: str, content: str, chapter_word_count: int, genre: str, platform: str) -> Dict[str, Any]:
        """解析审核结果"""
        # 计算实际字数
        actual_word_count = len(content)
        
        # 检查字数是否达标
        word_count_check = "通过" if actual_word_count >= chapter_word_count else "未通过"
        
        # 从响应中提取评分
        import re
        score_match = re.search(r'总体评分：(\d+\.?\d*)', response)
        if score_match:
            total_score = float(score_match.group(1))
        else:
            # 如果没有找到评分，基于字数计算一个基础分数
            base_score = 100
            if word_count_check == "未通过":
                # 字数不足，严重扣分
                word_count_ratio = actual_word_count / chapter_word_count
                if word_count_ratio < 0.5:
                    base_score -= 30
                elif word_count_ratio < 0.7:
                    base_score -= 20
                else:
                    base_score -= 10
            total_score = base_score
        
        # 从响应中提取问题
        issues = []
        issues_match = re.findall(r'问题：(.*?)(?=建议：|$)', response, re.DOTALL)
        for issue in issues_match:
            if issue.strip():
                issues.append(issue.strip())
        
        # 从响应中提取建议
        suggestions = []
        suggestions_match = re.findall(r'建议：(.*?)(?=问题：|$)', response, re.DOTALL)
        for suggestion in suggestions_match:
            if suggestion.strip():
                suggestions.append(suggestion.strip())
        
        # 构建审核结果
        audit_result = {
            "score": round(total_score, 2),
            "issues": issues,
            "suggestions": suggestions,
            "word_count": actual_word_count,
            "word_count_check": word_count_check,
            "analysis": response
        }
        
        # 如果字数不达标，添加问题和建议
        if word_count_check == "未通过":
            word_count_issue = f"字数不足，要求{chapter_word_count}字，实际{actual_word_count}字"
            if word_count_issue not in audit_result["issues"]:
                audit_result["issues"].append(word_count_issue)
            word_count_suggestion = f"建议增加{chapter_word_count - actual_word_count}字的内容，可以通过以下方式：1. 增加场景描写；2. 丰富人物对话；3. 详细描述人物心理活动；4. 增加情节细节"
            if word_count_suggestion not in audit_result["suggestions"]:
                audit_result["suggestions"].append(word_count_suggestion)
        
        return audit_result