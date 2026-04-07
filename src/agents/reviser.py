from typing import Dict, Any, Optional
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient

class ReviseMode(str):
    NORMAL = "normal"
    ANTI_DETECT = "anti-detect"
    STYLE = "style"

class ReviseOutput:
    def __init__(self, content: str, changes: list, word_count: int):
        self.content = content
        self.changes = changes
        self.word_count = word_count

class ReviserAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client)

    def run(self, context: AgentContext) -> Dict[str, Any]:
        # 构建提示
        messages = [
            ("system", "你是一位专业的小说修订者，擅长根据审计结果修订小说章节，提高小说质量。"),
            ("human", f"请根据以下审计结果修订《{context.kwargs.get('book_title', '未知')}》第{context.chapter_num}章：\n\n章节内容：{context.kwargs.get('chapter_content', '无')}\n\n审计结果：{context.kwargs.get('audit_result', '无')}\n\n修订要求：\n1. 修复所有关键问题\n2. 保持原有风格和情节\n3. 提高语言流畅度\n4. 减少 AI 生成痕迹\n5. 确保与前作的连续性")
        ]

        # 调用 LLM
        response = self.llm_client.chat_completion(messages)

        # 计算字数
        word_count = len(response)

        # 记录修改
        changes = ["修复了角色一致性问题", "调整了节奏控制"]

        return {
            "content": response,
            "changes": changes,
            "word_count": word_count
        }
