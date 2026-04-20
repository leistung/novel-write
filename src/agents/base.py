from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class AgentContext:
    def __init__(self, book_id: str, chapter_num: Optional[int] = None, **kwargs):
        self.book_id = book_id
        self.chapter_num = chapter_num
        self.kwargs = kwargs

class BaseAgent(ABC):
    def __init__(self, llm):
        self.llm = llm
        self.parser = StrOutputParser()
    
    def create_prompt(self, system_prompt: str, user_prompt: str) -> ChatPromptTemplate:
        """创建提示词模板"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
    
    def run_chain(self, prompt: ChatPromptTemplate, inputs: Dict[str, Any] = {}) -> Dict[str, Any]:
        """运行链"""
        # 不使用parser，直接获取完整的响应
        chain = prompt | self.llm
        response = chain.invoke(inputs)
        
        # 提取token使用情况
        token_usage = None
        if hasattr(response, 'usage_metadata'):
            token_usage = response.usage_metadata
        
        # 提取内容
        content = response.content
        
        return {
            'content': content,
            'token_usage': token_usage
        }
